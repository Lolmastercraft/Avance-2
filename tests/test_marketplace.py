import io
import os
import re
import secrets

import pytest
from PIL import Image
from sqlalchemy import select

from app.models import Base, CartItem, Notification, Order, Product, User
from app.web import create_app


class MemoryStorage:
    def __init__(self):
        self.images = {}

    def healthy(self):
        return None

    def put_image(self, data):
        from app.storage import Storage
        store = object.__new__(Storage)
        store.bucket = "test-bucket"
        outer = self

        class Client:
            def put_object(self, **kwargs):
                outer.images[kwargs["Key"]] = kwargs["Body"]
        store.client = Client()
        return store.put_image(data)

    def read_image(self, key):
        return self.images.get(key, b"test"), "image/jpeg"


@pytest.fixture
def app(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.sqlite'}"
    os.environ["DATABASE_URL"] = url
    application = create_app({"TESTING": True, "SECRET_KEY": secrets.token_hex(32),
                              "DATABASE_URL": url, "SESSION_COOKIE_SECURE": False}, MemoryStorage())
    Base.metadata.create_all(application.extensions["db_engine"])
    with application.extensions["db_factory"].begin() as db:
        db.add(Product(name="Producto de prueba", description="Catálogo", category="Tecnología",
                       price_cents=15000, stock=2, image_key="test.jpg"))
    yield application
    application.extensions["db_engine"].dispose()


def token(client, path="/registro"):
    html = client.get(path).text
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def register(client, email="test@example.test"):
    password = secrets.token_urlsafe(20)
    return client.post("/registro", data={"csrf_token": token(client), "name": "Prueba",
                       "email": email, "password": password}), password


def purchase(client):
    client.post("/carrito/agregar/1", data={"csrf_token": token(client, "/")})
    page = client.get("/carrito").text
    return client.post("/pedidos", data={"csrf_token": re.search(r'name="csrf_token" value="([^"]+)"', page).group(1),
                       "checkout_key": re.search(r'name="checkout_key" value="([^"]+)"', page).group(1),
                       "price": "0.01"})


def test_health_and_headers(app):
    result = app.test_client().get("/salud")
    assert result.json["status"] == "ok"
    assert result.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in result.headers["Content-Security-Policy"]


def test_health_fails_closed(app):
    app.extensions["storage"].healthy = lambda: (_ for _ in ()).throw(RuntimeError())
    assert app.test_client().get("/salud").status_code == 503


def test_csrf_blocks_forgery(app):
    assert app.test_client().post("/registro", data={"email": "x@y.test"}).status_code == 400


def test_authentication_and_password_hash(app):
    client = app.test_client()
    result, password = register(client)
    assert result.status_code == 302
    with app.extensions["db_factory"]() as db:
        user = db.scalar(select(User))
        assert password not in user.password_hash
        assert user.password_hash.startswith("scrypt:")
    client.post("/logout", data={"csrf_token": token(client, "/")})
    assert client.get("/pedidos").status_code == 302
    assert client.post("/login", data={"csrf_token": token(client, "/login"), "email": "test@example.test", "password": password}).status_code == 302


def test_wrong_password_rejected(app):
    client = app.test_client()
    register(client)
    client.post("/logout", data={"csrf_token": token(client, "/")})
    assert client.post("/login", data={"csrf_token": token(client, "/login"), "email": "test@example.test", "password": secrets.token_hex(10)}).status_code == 401


def test_checkout_uses_server_price_and_outbox(app):
    client = app.test_client()
    register(client)
    result = purchase(client)
    assert result.status_code == 302
    with app.extensions["db_factory"]() as db:
        assert db.scalar(select(Order)).total_cents == 15000
        assert db.get(Product, 1).stock == 1
        assert db.scalar(select(Notification)).status == "pendiente"
        assert db.scalar(select(CartItem)) is None
    from app.notifications import deliver_once
    assert deliver_once(app.extensions["db_factory"]) == 1
    assert deliver_once(app.extensions["db_factory"]) == 0
    assert "Confirmación enviada" in client.get(result.location).text


def test_order_isolation(app):
    alice, bob = app.test_client(), app.test_client()
    register(alice, "alice@example.test")
    result = purchase(alice)
    register(bob, "bob@example.test")
    assert bob.get(result.location).status_code == 404


def test_stock_limit(app):
    client = app.test_client()
    register(client)
    csrf = token(client, "/")
    for _ in range(2):
        assert client.post("/carrito/agregar/1", data={"csrf_token": csrf}).status_code == 302
    assert client.post("/carrito/agregar/1", data={"csrf_token": csrf}).status_code == 409


def test_checkout_transaction_rolls_back(app):
    client = app.test_client()
    register(client)
    client.post("/carrito/agregar/1", data={"csrf_token": token(client, "/")})
    page = client.get("/carrito").text
    with app.extensions["db_factory"].begin() as db:
        db.get(Product, 1).stock = 0
    result = client.post("/pedidos", data={"csrf_token": re.search(r'name="csrf_token" value="([^"]+)"', page).group(1), "checkout_key": re.search(r'name="checkout_key" value="([^"]+)"', page).group(1)})
    assert result.status_code == 409
    with app.extensions["db_factory"]() as db:
        assert db.scalar(select(Order)) is None
        assert db.scalar(select(Notification)) is None


def test_sql_injection_is_data(app):
    response = app.test_client().get("/", query_string={"q": "' OR 1=1 --"})
    assert response.status_code == 200
    assert "No encontramos productos" in response.text


def test_xss_escaped(app):
    with app.extensions["db_factory"].begin() as db:
        db.get(Product, 1).name = "<script>alert(1)</script>"
    response = app.test_client().get("/")
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_images_validate_content(app):
    store = app.extensions["storage"]
    with pytest.raises(ValueError):
        store.put_image(b"<script>not an image</script>")
    data = io.BytesIO()
    Image.new("RGB", (30, 30)).save(data, "PNG")
    key = store.put_image(data.getvalue())
    assert store.images[key].startswith(b"\xff\xd8")


def test_sell_uploads_and_persists(app):
    client = app.test_client()
    register(client)
    data = io.BytesIO()
    Image.new("RGB", (30, 30)).save(data, "PNG")
    data.seek(0)
    response = client.post("/vender", data={"csrf_token": token(client, "/vender"), "name": "Nuevo producto", "description": "Prueba", "category": "Accesorios", "price": "123.45", "stock": "5", "image": (data, "test.png")})
    assert response.status_code == 302
    with app.extensions["db_factory"]() as db:
        product = db.scalar(select(Product).where(Product.name == "Nuevo producto"))
        assert product.price_cents == 12345
        assert product.image_key in app.extensions["storage"].images
