from flask import Blueprint, jsonify
from models.business import Business
from models.category import Category
from models.product import Product

menu_bp = Blueprint("menu", __name__)

@menu_bp.route("/<slug>", methods=["GET"])
def get_menu(slug):
    business = Business.query.filter_by(slug=slug).first_or_404()

    categories = Category.query.filter_by(business_id=business.id).all()

    result = []
    for cat in categories:
        products = Product.query.filter_by(category_id=cat.id, available=True).all()
        result.append({
            "id": cat.id,
            "name": cat.name,
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
            "primary_color": business.primary_color,
            "secondary_color": business.secondary_color
        },
        "categories": result
    })