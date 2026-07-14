from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.business import Business
from models.category import Category
from models.product import Product
from models.recipe import Recipe

recipes_bp = Blueprint("recipes", __name__)


def _business_products_query(business_id):
    return (
        Product.query
        .join(Category, Product.category_id == Category.id)
        .filter(Category.business_id == business_id)
    )


@recipes_bp.route("/search", methods=["GET"])
@jwt_required()
def search_products():
    business_id = int(get_jwt_identity())
    q = request.args.get("q", "").strip()

    if not q:
        return jsonify([])

    products = (
        _business_products_query(business_id)
        .filter(Product.name.ilike(f"%{q}%"))
        .order_by(Product.name.asc())
        .limit(10)
        .all()
    )

    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "category_name": p.category.name
        }
        for p in products
    ])


@recipes_bp.route("/product/<int:product_id>", methods=["GET"])
@jwt_required()
def get_recipe(product_id):
    business_id = int(get_jwt_identity())

    product = (
        _business_products_query(business_id)
        .filter(Product.id == product_id)
        .first_or_404()
    )

    recipe = product.recipe

    return jsonify({
        "product_id": product.id,
        "product_name": product.name,
        "image_url": product.image_url,
        "ingredients": recipe.ingredients if recipe else "",
        "procedure": recipe.procedure if recipe else "",
        "has_recipe": recipe is not None
    })


@recipes_bp.route("/product/<int:product_id>", methods=["PUT"])
@jwt_required()
def save_recipe(product_id):
    business_id = int(get_jwt_identity())
    business = Business.query.get_or_404(business_id)

    product = (
        _business_products_query(business_id)
        .filter(Product.id == product_id)
        .first_or_404()
    )

    data = request.get_json()
    pin = str(data.get("pin", "")).strip()

    if not business.recipe_pin:
        return jsonify({"error": "Este negocio no tiene un PIN configurado."}), 400

    if pin != business.recipe_pin:
        return jsonify({"error": "PIN incorrecto"}), 403

    recipe = product.recipe

    if not recipe:
        recipe = Recipe(product_id=product.id)
        db.session.add(recipe)

    recipe.ingredients = data.get("ingredients", "")
    recipe.procedure = data.get("procedure", "")

    db.session.commit()

    return jsonify({"message": "Receta guardada correctamente"})

@recipes_bp.route("/verify-pin", methods=["POST"])
@jwt_required()
def verify_recipe_pin():
    business_id = int(get_jwt_identity())
    business = Business.query.get_or_404(business_id)

    data = request.get_json()
    pin = str(data.get("pin", "")).strip()

    if not business.recipe_pin:
        return jsonify({
            "error": "Este negocio no tiene un PIN configurado."
        }), 400

    if pin != business.recipe_pin:
        return jsonify({
            "error": "PIN incorrecto"
        }), 403

    return jsonify({
        "message": "PIN válido"
    }), 200