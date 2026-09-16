"""Catálogo, autenticación, carrito y checkout transaccional."""
import io
import os
import re
import secrets
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import Base, CartItem, Notification, Order, OrderItem, Product, User, database
from app.storage import Storage


def create_app(config=None, storage=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"), MAX_CONTENT_LENGTH=2 * 1024 * 1024 + 65536,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "true").lower() == "true",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2), WTF_CSRF_TIME_LIMIT=3600,
    )
    if config:
        app.config.update(config)
    if not app.config["SECRET_KEY"] or len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError("SECRET_KEY debe contener al menos 32 caracteres aleatorios.")
    engine, factory = database(app.config.get("DATABASE_URL"))
    app.extensions["db_engine"] = engine
    app.extensions["db_factory"] = factory
    app.extensions["storage"] = storage or Storage()
    CSRFProtect(app)
    limiter = Limiter(get_remote_address, app=app, default_limits=["180 per minute"],
                      storage_uri="memory://", enabled=not app.config.get("TESTING"))
    app.extensions["market_limiter"] = limiter
    # Only the Compose proxy reaches this port; one trusted proxy hop.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    @app.before_request
    def load_user():
        g.user = None
        if session.get("user_id"):
            with factory() as db:
                g.user = db.get(User, session["user_id"])

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    @app.after_request
    def headers(response):
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store" if g.get("user") else "no-cache"
        return response

    @app.context_processor
    def helpers():
        count = 0
        if g.get("user"):
            with factory() as db:
                count = sum(x.quantity for x in db.scalars(select(CartItem).where(CartItem.user_id == g.user.id)))
        return {"cart_count": count, "money": lambda cents: f"${cents / 100:,.2f}"}

    @app.get("/salud")
    @limiter.exempt
    def health():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            app.extensions["storage"].healthy()
            return jsonify(status="ok", service="marketplace-api", database="ok", s3="ok")
        except Exception:
            app.logger.error("Health dependency unavailable")
            return jsonify(status="degraded", service="marketplace-api"), 503

    @app.get("/")
    def catalog():
        query = request.args.get("q", "").strip()[:80]
        category = request.args.get("categoria", "")
        statement = select(Product).order_by(Product.id)
        if query:
            statement = statement.where(Product.name.ilike(f"%{query}%"))
        if category:
            statement = statement.where(Product.category == category)
        with factory() as db:
            products = db.scalars(statement).all()
        return render_template("catalog.html", products=products, query=query, category=category)

    @app.get("/imagenes/<int:product_id>")
    def image(product_id):
        with factory() as db:
            product = db.get(Product, product_id)
            if not product:
                abort(404)
            key = product.image_key
        data, content_type = app.extensions["storage"].read_image(key)
        return send_file(io.BytesIO(data), mimetype=content_type, max_age=300)

    @app.route("/registro", methods=["GET", "POST"])
    @limiter.limit("10 per minute")
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not 2 <= len(name) <= 80 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254 or not 12 <= len(password) <= 128:
                flash("Escribe tu nombre, un correo válido y una contraseña de 12 a 128 caracteres.", "error")
                return render_template("auth.html", register=True), 400
            try:
                with factory.begin() as db:
                    user = User(name=name, email=email, password_hash=generate_password_hash(password))
                    db.add(user)
                    db.flush()
                    user_id = user.id
            except IntegrityError:
                flash("No se pudo registrar ese correo. Intenta iniciar sesión.", "error")
                return render_template("auth.html", register=True), 409
            session.clear()
            session["user_id"] = user_id
            session.permanent = True
            flash("Tu cuenta está lista. Encuentra algo que te guste.", "success")
            return redirect(url_for("catalog"))
        return render_template("auth.html", register=True)

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("10 per minute")
    def login():
        if request.method == "POST":
            with factory() as db:
                user = db.scalar(select(User).where(User.email == request.form.get("email", "").strip().lower()))
                password = request.form.get("password", "")
                if not user or len(password) > 128 or not check_password_hash(user.password_hash, password):
                    flash("Correo o contraseña incorrectos.", "error")
                    return render_template("auth.html", register=False), 401
                user_id = user.id
            session.clear()
            session["user_id"] = user_id
            session.permanent = True
            return redirect(url_for("catalog"))
        return render_template("auth.html", register=False)

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("catalog"))

    @app.post("/carrito/agregar/<int:product_id>")
    @login_required
    def add_cart(product_id):
        with factory.begin() as db:
            db.scalar(select(User).where(User.id == g.user.id).with_for_update())
            product = db.get(Product, product_id)
            if not product:
                abort(404)
            row = db.scalar(select(CartItem).where(CartItem.user_id == g.user.id, CartItem.product_id == product_id))
            quantity = (row.quantity if row else 0) + 1
            if quantity > min(product.stock, 10):
                abort(409, "No hay más unidades disponibles para este carrito.")
            if row:
                row.quantity = quantity
            else:
                db.add(CartItem(user_id=g.user.id, product_id=product_id, quantity=1))
        flash("Producto agregado al carrito.", "success")
        return redirect(url_for("cart"))

    @app.get("/carrito")
    @login_required
    def cart():
        session.setdefault("checkout_key", secrets.token_hex(24))
        with factory() as db:
            rows = db.execute(select(CartItem, Product).join(Product).where(CartItem.user_id == g.user.id)).all()
        return render_template("cart.html", rows=rows, total=sum(c.quantity * p.price_cents for c, p in rows))

    @app.post("/carrito/quitar/<int:item_id>")
    @login_required
    def remove_cart(item_id):
        with factory.begin() as db:
            db.scalar(select(User).where(User.id == g.user.id).with_for_update())
            db.execute(delete(CartItem).where(CartItem.id == item_id, CartItem.user_id == g.user.id))
        return redirect(url_for("cart"))

    @app.post("/pedidos")
    @login_required
    def checkout():
        key = request.form.get("checkout_key", "")
        if not key or not secrets.compare_digest(key, session.get("checkout_key", "")):
            abort(400, "Actualiza el carrito antes de confirmar.")
        with factory.begin() as db:
            db.scalar(select(User).where(User.id == g.user.id).with_for_update())
            previous = db.scalar(select(Order).where(Order.request_key == key, Order.user_id == g.user.id))
            if previous:
                return redirect(url_for("order_detail", order_id=previous.id))
            cart_items = db.scalars(select(CartItem).where(CartItem.user_id == g.user.id).order_by(CartItem.product_id)).all()
            if not cart_items:
                abort(409, "Tu carrito está vacío.")
            order = Order(user_id=g.user.id, total_cents=0, request_key=key)
            db.add(order)
            db.flush()
            for row in cart_items:
                product = db.scalar(select(Product).where(Product.id == row.product_id).with_for_update())
                if not product or product.stock < row.quantity:
                    abort(409, "El inventario cambió. Revisa el carrito.")
                product.stock -= row.quantity
                order.total_cents += row.quantity * product.price_cents
                db.add(OrderItem(order_id=order.id, product_name=product.name, quantity=row.quantity, unit_cents=product.price_cents))
                db.delete(row)
            db.add(Notification(order_id=order.id))
            order_id = order.id
        return redirect(url_for("order_detail", order_id=order_id))

    @app.get("/pedidos")
    @login_required
    def orders():
        with factory() as db:
            items = db.scalars(select(Order).where(Order.user_id == g.user.id).order_by(Order.id.desc())).all()
        return render_template("orders.html", orders=items)

    @app.get("/pedidos/<int:order_id>")
    @login_required
    def order_detail(order_id):
        with factory() as db:
            order = db.scalar(select(Order).where(Order.id == order_id, Order.user_id == g.user.id))
            if not order:
                abort(404)
            items = db.scalars(select(OrderItem).where(OrderItem.order_id == order_id)).all()
            notice = db.scalar(select(Notification).where(Notification.order_id == order_id))
        session["checkout_key"] = secrets.token_hex(24)
        return render_template("order.html", order=order, items=items, notice=notice)

    @app.route("/vender", methods=["GET", "POST"])
    @login_required
    def sell():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            category = request.form.get("category", "")
            try:
                price = Decimal(request.form.get("price", "0"))
                stock = int(request.form.get("stock", "0"))
                if not price.is_finite() or price != price.quantize(Decimal("0.01")) or not Decimal("1") <= price <= Decimal("100000") or not 1 <= stock <= 1000 or not 3 <= len(name) <= 120 or len(description) > 500 or category not in {"Tecnología", "Escritorio", "Accesorios"}:
                    raise ValueError("Revisa nombre, categoría, precio y existencias.")
                upload = request.files.get("image")
                if not upload:
                    raise ValueError("Agrega una imagen del producto.")
                key = app.extensions["storage"].put_image(upload.read(2 * 1024 * 1024 + 1))
            except (ValueError, InvalidOperation) as error:
                flash(str(error), "error")
                return render_template("sell.html"), 400
            with factory.begin() as db:
                db.add(Product(name=name, description=description, category=category, price_cents=int(price * 100), stock=stock, image_key=key, seller_id=g.user.id))
            flash("Publicación creada. La imagen se guardó en S3.", "success")
            return redirect(url_for("catalog"))
        return render_template("sell.html")

    @app.errorhandler(HTTPException)
    def http_error(error):
        return render_template("error.html", code=error.code, message=error.description), error.code

    return app
