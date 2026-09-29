"""Adaptador del parche docente a los modelos existentes de Mercado Nube."""
from flask import current_app
from sqlalchemy import select

from app.models import Order, OrderItem, User


def obtener_pedido_por_id(pedido_id):
    with current_app.extensions["db_factory"]() as db:
        pedido = db.get(Order, pedido_id)
        if pedido is None:
            return None
        comprador = db.get(User, pedido.user_id)
        items = db.scalars(select(OrderItem).where(OrderItem.order_id == pedido.id)).all()
        return {"id": pedido.id, "user_id": pedido.user_id, "correo_comprador": comprador.email,
                "detalle": "\n".join(f"{i.product_name} x {i.quantity}" for i in items)
                + f"\nTotal: ${pedido.total_cents / 100:.2f} MXN"}
