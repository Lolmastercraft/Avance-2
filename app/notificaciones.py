"""Correo SMTP capturado en el buzón privado de pruebas; no sale a Internet."""
import smtplib
from email.message import EmailMessage

from flask import current_app


def enviar_correo_confirmacion(destinatario, numero_pedido, detalle):
    sender = current_app.extensions.get("confirmation_sender")
    if sender:
        return sender(destinatario=destinatario, numero_pedido=numero_pedido, detalle=detalle)
    message = EmailMessage()
    message["From"] = "Mercado Nube <confirmaciones@mercado-nube.test>"
    message["To"] = destinatario
    message["Subject"] = f"Confirmacion de pedido MN-{numero_pedido:05d}"
    message.set_content(f"Tu pedido MN-{numero_pedido:05d} esta confirmado.\n\n{detalle}\n\nBuzon de pruebas de la entrega final. No se envia a proveedores externos.")
    with smtplib.SMTP("mailpit", 1025, timeout=10) as smtp:
        smtp.send_message(message)
