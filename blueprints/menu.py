from flask import Blueprint, jsonify
from models.business import Business
from models.category import Category
from models.product import Product

menu_bp = Blueprint("menu", __name__)

@menu_bp.route("/<slug>", methods=["GET"])
def get_menu(slug):
    business = Business.query.filter_by(slug=slug).first_or_404()

    # Categorías ordenadas
    categories = (
        Category.query
        .filter_by(
            business_id=business.id,
            parent_id=None
        )
        .order_by(Category.display_order.asc())
        .all()
    )

    result = []

    for cat in categories:

        # Productos ordenados
        products = (
            Product.query
            .filter_by(category_id=cat.id, available=True)
            .order_by(Product.display_order.asc())
            .all()
        )

        result.append({
            "id": cat.id,
            "name": cat.name,
            "emoji": cat.emoji,
            "image_url": cat.image_url,
            "has_subcategories": len(cat.children) > 0,
            "products": [{
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "image_url": p.image_url
            } for p in products]
        })

    return jsonify({
        "business": {
            "name": business.name,
            "logo_url": business.logo_url,
            "tagline": business.tagline,
            "banner_url": business.banner_url,
            "accent_color": business.accent_color,
            "background_color": business.background_color,
            "text_color": business.text_color,
            "font_key": business.font_key
        },
        "categories": result
    })


@menu_bp.route("/<slug>/category/<int:category_id>", methods=["GET"])
def get_category(slug, category_id):
    business = Business.query.filter_by(slug=slug).first_or_404()

    category = Category.query.filter_by(
        id=category_id,
        business_id=business.id
    ).first_or_404()

    products = (
        Product.query
        .filter_by(
            category_id=category.id,
            available=True
        )
        .order_by(Product.display_order.asc())
        .all()
    )

    return jsonify({
        "business": {
            "name": business.name,
            "logo_url": business.logo_url,
            "tagline": business.tagline,
            "banner_url": business.banner_url,
            "accent_color": business.accent_color,
            "background_color": business.background_color,
            "text_color": business.text_color,
            "font_key": business.font_key
        },
        "category": {
            "id": category.id,
            "name": category.name,
            "emoji": category.emoji,
            "image_url": category.image_url,
            "has_subcategories": len(category.children) > 0,
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price,
                    "image_url": p.image_url
                }
                for p in products
            ]
        }
    })