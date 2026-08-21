"""
services/claude_agent.py

Orquesta la conversación con Claude para el agente de WhatsApp:
- Arma el system prompt y el historial
- Llama a la API de Anthropic con las tools disponibles
- Si Claude pide ejecutar una tool, la corre y le devuelve el resultado
- Devuelve el texto final de respuesta para enviar al cliente
"""

import os
import json
import anthropic

from services.tools_wpp_agent import (
    TOOLS_DEFINITION,
    consultar_menu,
    crear_pedido,
)

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT_TEMPLATE = """Eres el asistente de WhatsApp de {business_name}, un café-bar.

Tu único propósito es:
1. Responder preguntas sobre los productos del menú (usando siempre la herramienta consultar_menu, nunca inventes productos ni precios).
2. Tomar pedidos cuando el cliente ya decidió qué quiere, usando la herramienta crear_pedido.

Reglas importantes:
- Sé breve, cálido y natural, como alguien que atiende un café. No uses lenguaje robótico ni listas largas innecesarias.
- Cuando el cliente pregunte por el menú o productos, incluye el link de la carta digital (viene en la respuesta de consultar_menu como "menu_url").
- Nunca inventes disponibilidad, precios ni productos que no vengan de consultar_menu.
- Antes de crear un pedido, confirma con el cliente qué productos y cantidades quiere.
- Después de crear un pedido, informa claramente que el pedido quedó pendiente de aprobación del negocio, y que le avisarás en cuanto se confirme. Nunca digas que el pedido ya está confirmado.
- Si el cliente pregunta algo fuera de productos o pedidos (quejas, temas administrativos, etc.), indícale amablemente que un miembro del equipo lo va a contactar.
"""


def _ejecutar_tool(tool_name: str, tool_input: dict, business_id: int, customer_phone: str) -> dict:
    """
    Despacha la ejecución real de cada tool. business_id y customer_phone
    los inyectamos nosotros, nunca los decide el modelo.
    """
    if tool_name == "consultar_menu":
        return consultar_menu(
            business_id=business_id,
            categoria=tool_input.get("categoria"),
        )
    if tool_name == "crear_pedido":
        return crear_pedido(
            business_id=business_id,
            customer_phone=customer_phone,
            items=tool_input.get("items", []),
        )
    return {"error": f"Tool desconocida: {tool_name}"}


def generar_respuesta(business_name: str, business_id: int, customer_phone: str, historial: list[dict]) -> str:
    """
    historial: lista de mensajes previos en formato [{"role": "user"|"assistant", "content": str}, ...]
    incluyendo ya el mensaje nuevo del cliente al final.

    Devuelve el texto final que se le debe enviar al cliente por WhatsApp.
    """
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(business_name=business_name)
    messages = list(historial)

    # Loop de tool use: Claude puede pedir ejecutar una o varias tools
    # antes de dar la respuesta final en texto.
    for _ in range(5):  # límite de seguridad para evitar loops infinitos
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS_DEFINITION,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            # Respuesta final en texto
            texto_final = "".join(
                block.text for block in response.content if block.type == "text"
            )
            return texto_final.strip()

        # Claude pidió usar una o más tools: las ejecutamos todas
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                resultado = _ejecutar_tool(
                    tool_name=block.name,
                    tool_input=block.input,
                    business_id=business_id,
                    customer_phone=customer_phone,
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                })

        messages.append({"role": "user", "content": tool_results})

    return "Disculpa, tuve un problema procesando tu mensaje. En un momento te contacta alguien del equipo."