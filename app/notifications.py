"""Worker separado: consume outbox de RDS y confirma pedidos de forma idempotente."""
import json
import time

from flask import Flask, jsonify
from sqlalchemy import select, text

from app.models import Notification, Order, database, now

engine, factory = database()


def deliver_once(sessions=factory):
    with sessions.begin() as db:
        pending = db.scalars(select(Notification).where(Notification.status == "pendiente")
                             .order_by(Notification.id).limit(20).with_for_update(skip_locked=True)).all()
        for notice in pending:
            order = db.get(Order, notice.order_id)
            notice.message = f"Tu pedido MN-{order.id:05d} por ${order.total_cents / 100:,.2f} MXN está confirmado. Gracias por comprar en Mercado Nube."
            notice.status = "enviada"
            notice.delivered_at = now()
        count = len(pending)
    if count:
        print(json.dumps({"event": "notifications_delivered", "count": count}), flush=True)
    return count


def create_worker():
    import threading
    app = Flask(__name__)
    state = {"heartbeat": time.monotonic()}

    def consume():
        while True:
            try:
                deliver_once()
                state["heartbeat"] = time.monotonic()
            except Exception:
                app.logger.error("Notification transaction failed; retry scheduled")
            time.sleep(2)

    threading.Thread(target=consume, daemon=True).start()

    @app.get("/salud")
    def health():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            if time.monotonic() - state["heartbeat"] > 30:
                raise RuntimeError("Worker not progressing")
            return jsonify(status="ok", service="notifications", mode="simulated-outbox")
        except Exception:
            return jsonify(status="degraded"), 503

    return app
