"""
blueprints/whatsapp_webhook.py

Rutas del webhook de WhatsApp Business (Meta):
- GET  /webhook/whatsapp  -> verificación inicial que hace Meta
- POST /webhook/whatsapp  -> recepción de mensajes entrantes de clientes
"""

import os
from flask import Blueprint, request, jsonify

from app import db
from models.models_wpp_agent import BusinessWhatsAppConfig, ConversationHistory
from services.claude_agent import generar_respuesta
from services.whatsapp_client import enviar_mensaje_texto

whatsapp_webhook_bp = Blueprint("whatsapp_webhook", __name__)

VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]

# Cuántos mensajes previos (user/assistant) se cargan como contexto para Claude
HISTORIAL_LIMITE = 20


@whatsapp_webhook_bp.route("/webhook/whatsapp", methods=["GET"])
def verificar_webhook():
    """
    Meta llama a este endpoint una sola vez al configurar el webhook,
    para confirmar que la URL es tuya.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Token de verificación inválido", 403


@whatsapp_webhook_bp.route("/webhook/whatsapp", methods=["POST"])
def recibir_mensaje():
    """
    Recibe mensajes entrantes de clientes, los procesa con Claude,
    y responde por WhatsApp.
    """
    data = request.get_json(silent=True) or {}

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]["value"]

        # Meta también manda notificaciones de "status" (entregado, leído, etc.)
        # que no traen "messages" — las ignoramos.
        if "messages" not in change:
            return jsonify({"status": "ignored"}), 200

        phone_number_id = change["metadata"]["phone_number_id"]
        mensaje = change["messages"][0]
        customer_phone = mensaje["from"]
        texto_cliente = mensaje.get("text", {}).get("body", "")

    except (KeyError, IndexError):
        return jsonify({"status": "invalid_payload"}), 200

    if not texto_cliente:
        # Por ahora solo manejamos mensajes de texto (no audios, imágenes, etc.)
        return jsonify({"status": "unsupported_message_type"}), 200

    config = BusinessWhatsAppConfig.query.filter_by(
        phone_number_id=phone_number_id, active=True
    ).first()

    if not config:
        return jsonify({"status": "business_not_found"}), 200

    business = config.business

    # Guardar el mensaje del cliente en el historial
    db.session.add(ConversationHistory(
        business_id=business.id,
        customer_phone=customer_phone,
        role="user",
        content=texto_cliente,
    ))
    db.session.commit()

    # Cargar historial reciente para dar contexto a Claude
    historial_db = (
        ConversationHistory.query
        .filter_by(business_id=business.id, customer_phone=customer_phone)
        .filter(ConversationHistory.role.in_(["user", "assistant"]))
        .order_by(ConversationHistory.created_at.desc())
        .limit(HISTORIAL_LIMITE)
        .all()
    )
    historial_db.reverse()  # orden cronológico

    historial = [
        {"role": h.role, "content": h.content} for h in historial_db
    ]

    respuesta_texto = generar_respuesta(
        business_name=business.name,
        business_id=business.id,
        customer_phone=customer_phone,
        historial=historial,
    )

    # Guardar la respuesta del agente en el historial
    db.session.add(ConversationHistory(
        business_id=business.id,
        customer_phone=customer_phone,
        role="assistant",
        content=respuesta_texto,
    ))
    db.session.commit()

    enviar_mensaje_texto(
        phone_number_id=config.phone_number_id,
        access_token=config.access_token,
        to=customer_phone,
        texto=respuesta_texto,
    )

    return jsonify({"status": "ok"}), 200