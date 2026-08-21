"""
services/whatsapp_client.py

Funciones para enviar mensajes salientes a través de la API de WhatsApp
Business Cloud (Meta Graph API).
"""

import requests

GRAPH_API_VERSION = "v20.0"


def enviar_mensaje_texto(phone_number_id: str, access_token: str, to: str, texto: str) -> dict:
    """
    Envía un mensaje de texto simple.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": texto},
    }
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()