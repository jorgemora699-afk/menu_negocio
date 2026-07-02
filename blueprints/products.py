from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.product import Product
from models.category import Category
from app import db

products_bp = Blueprint("products", __name__)

@products_bp.route("/", methods=["GET"])
@jwt_required()
def get_products():
    business_id = int(get_jwt_identity())
    category_id = request.args.get("category_id")
    query = Product.query.join(Category).filter(Category.business_id == business_id)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    products = query.order_by(Product.display_order.asc()).all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "image_url": p.image_url,
        "available": p.available,
        "category_id": p.category_id,
        "display_order": p.display_order
    } for p in products])

@products_bp.route("/", methods=["POST"])
@jwt_required()
def create_product():
    business_id = int(get_jwt_identity())
    data = request.get_json()
    category = Category.query.filter_by(id=data["category_id"], business_id=business_id).first_or_404()
    last_product = Product.query.filter_by(
        category_id=category.id
    ).order_by(Product.display_order.desc()).first()

    next_order = (
        last_product.display_order + 1
        if last_product
        else 1
    )

    product = Product(
        name=data["name"],
        description=data.get("description", ""),
        price=data["price"],
        image_url=data.get("image_url", ""),
        available=data.get("available", True),
        category_id=category.id,
        display_order=next_order
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"id": product.id, "name": product.name}), 201

@products_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_product(id):
    business_id = int(get_jwt_identity())
    product = Product.query.join(Category).filter(Product.id == id, Category.business_id == business_id).first_or_404()
    data = request.get_json()
    product.name = data.get("name", product.name)
    product.description = data.get("description", product.description)
    product.price = data.get("price", product.price)
    product.image_url = data.get("image_url", product.image_url)
    product.available = data.get("available", product.available)
    product.category_id = data.get("category_id", product.category_id)
    db.session.commit()
    return jsonify({"id": product.id, "name": product.name})

@products_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_product(id):
    business_id = int(get_jwt_identity())
    product = Product.query.join(Category).filter(Product.id == id, Category.business_id == business_id).first_or_404()
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Producto eliminado"})

@products_bp.route("/<int:id>/move-up", methods=["PUT"])
@jwt_required()
def move_product_up(id):
    business_id = int(get_jwt_identity())

    product = Product.query.join(Category).filter(
        Product.id == id,
        Category.business_id == business_id
    ).first_or_404()

    previous = Product.query.filter(
        Product.category_id == product.category_id,
        Product.display_order < product.display_order
    ).order_by(Product.display_order.desc()).first()

    if previous:
        product.display_order, previous.display_order = (
            previous.display_order,
            product.display_order
        )
        db.session.commit()

    return jsonify({"message": "ok"})

@products_bp.route("/<int:id>/move-down", methods=["PUT"])
@jwt_required()
def move_product_down(id):
    business_id = int(get_jwt_identity())

    product = Product.query.join(Category).filter(
        Product.id == id,
        Category.business_id == business_id
    ).first_or_404()

    nxt = Product.query.filter(
        Product.category_id == product.category_id,
        Product.display_order > product.display_order
    ).order_by(Product.display_order.asc()).first()

    if nxt:
        product.display_order, nxt.display_order = (
            nxt.display_order,
            product.display_order
        )
        db.session.commit()

    return jsonify({"message": "ok"})