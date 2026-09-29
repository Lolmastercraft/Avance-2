"""
PARCHE - Nueva funcionalidad: reenviar confirmacion de un pedido
Tema: Marketplace

Producto pide: si al comprador se le paso el correo de confirmacion de su
pedido, que pueda pedir que se lo reenvien desde la app. Integra este
endpoint en tu servicio de notificaciones (o donde manejes los pedidos).
"""
from flask import Blueprint, jsonify
from app.db import obtener_pedido_por_id
from app.notificaciones import enviar_correo_confirmacion

reenviar_bp = Blueprint("reenviar", __name__)


@reenviar_bp.route("/pedidos/<int:pedido_id>/reenviar-confirmacion", methods=["POST"])
def reenviar_confirmacion(pedido_id):
    """Reenvia el correo de confirmacion de un pedido ya existente."""
    pedido = obtener_pedido_por_id(pedido_id)

    if pedido is None:
        return jsonify({"error": "pedido no encontrado"}), 404

    enviar_correo_confirmacion(
        destinatario=pedido["correo_comprador"],
        numero_pedido=pedido["id"],
        detalle=pedido["detalle"],
    )

    return jsonify({"mensaje": f"Confirmacion reenviada para el pedido {pedido_id}"})
