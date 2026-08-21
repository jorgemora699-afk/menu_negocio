"""
tools_wpp_agent.py

Funciones reales (ejecutadas contra la BD) que el agente de Claude puede invocar,
más sus definiciones en formato Anthropic tool-use.
"""

from app import db
from models.product import Product
from models.category import Category
from models.business import Business
from models.models_wpp_agent import Order

MENU_BASE_URL = "https://qrmenu-frontend-roan.vercel.app"


# ---------------------------------------------------------------------------
# 1. Consultar menú
# ---------------------------------------------------------------------------

def consultar_menu(business_id: int, categoria: str | None = None) -> dict:
    """
    Devuelve los productos disponibles de un negocio, opcionalmente filtrados
    por categoría (búsqueda parcial, insensible a mayúsculas).
    """
    query = (
        db.session.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.business_id == business_id)
        .filter(Product.available.is_(True))
    )

    if categoria:
        query = query.filter(Category.name.ilike(f"%{categoria}%"))

    productos = query.order_by(Category.id, Product.display_order).all()

    if not productos:
        return {
            "encontrado": False,
            "mensaje": "No se encontraron productos disponibles con ese criterio."
        }

    resultado_por_categoria: dict[str, list[dict]] = {}
    for p in productos:
        cat_nombre = p.category.name
        resultado_por_categoria.setdefault(cat_nombre, []).append({
            "product_id": p.id,
            "nombre": p.name,
            "descripcion": p.description or "",
            "precio": float(p.price),
        })

    business = db.session.get(Business, business_id)
    menu_url = f"{MENU_BASE_URL}/{business.slug}" if business else None

    return {
        "encontrado": True,
        "categorias": resultado_por_categoria,
        "menu_url": menu_url,
    }


# ---------------------------------------------------------------------------
# 2. Crear pedido
# ---------------------------------------------------------------------------

def crear_pedido(business_id: int, customer_phone: str, items: list[dict]) -> dict:
    """
    items esperado: [{"product_id": int, "quantity": int, "notes": str (opcional)}, ...]

    Valida cada producto contra la BD (nunca confía en nombres/precios que
    pudiera inventar el modelo), calcula el total real, y crea el pedido
    en estado 'pendiente_aprobacion'.
    """
    if not items:
        return {"exito": False, "error": "El pedido no tiene productos."}

    items_confirmados = []
    total = 0

    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)
        notes = item.get("notes", "")

        if not product_id or quantity < 1:
            return {"exito": False, "error": f"Item inválido: {item}"}

        producto = (
            db.session.query(Product)
            .join(Category, Product.category_id == Category.id)
            .filter(Product.id == product_id)
            .filter(Category.business_id == business_id)
            .filter(Product.available.is_(True))
            .first()
        )

        if not producto:
            return {
                "exito": False,
                "error": f"El producto con id {product_id} no existe o no está disponible."
            }

        subtotal = float(producto.price) * quantity
        total += subtotal

        items_confirmados.append({
            "product_id": producto.id,
            "name": producto.name,
            "quantity": quantity,
            "unit_price": float(producto.price),
            "notes": notes,
        })

    pedido = Order(
        business_id=business_id,
        customer_phone=customer_phone,
        items=items_confirmados,
        total=total,
        status="pendiente_aprobacion",
    )
    db.session.add(pedido)
    db.session.commit()

    return {
        "exito": True,
        "order_id": pedido.id,
        "items": items_confirmados,
        "total": total,
        "status": pedido.status,
    }


# ---------------------------------------------------------------------------
# Definiciones de tools en formato Anthropic
# ---------------------------------------------------------------------------

TOOLS_DEFINITION = [
    {
        "name": "consultar_menu",
        "description": (
            "Consulta el menú del negocio en tiempo real. Úsala cada vez que el "
            "cliente pregunte por productos, precios, categorías o disponibilidad. "
            "No inventes productos ni precios: siempre usa esta herramienta primero."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "categoria": {
                    "type": "string",
                    "description": (
                        "Categoría a filtrar (ej. 'bebidas calientes', 'postres'). "
                        "Opcional: si no se especifica, devuelve el menú completo."
                    ),
                }
            },
            "required": [],
        },
    },
    {
        "name": "crear_pedido",
        "description": (
            "Crea un pedido con los productos que el cliente confirmó que quiere. "
            "Úsala solo cuando el cliente haya confirmado explícitamente su pedido "
            "completo. El pedido queda pendiente de aprobación del negocio, así que "
            "informa al cliente que su pedido está siendo revisado, no que ya está confirmado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer"},
                            "quantity": {"type": "integer"},
                            "notes": {"type": "string"},
                        },
                        "required": ["product_id", "quantity"],
                    },
                }
            },
            "required": ["items"],
        },
    },
]