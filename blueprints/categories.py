from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.category import Category
from app import db

categories_bp = Blueprint("categories", __name__)

@categories_bp.route("/", methods=["GET"])
@jwt_required()
def get_categories():
    business_id = int(get_jwt_identity())
    categories = (
        Category.query
        .filter_by(
            business_id=business_id,
            parent_id=None
        )
        .order_by(Category.display_order.asc())
        .all()
    )
    return jsonify([
        {
            "id": c.id,
            "name": c.name,
            "emoji": c.emoji,
            "image_url": c.image_url,
            "display_order": c.display_order
        }
        for c in categories
    ])

@categories_bp.route("/", methods=["POST"])
@jwt_required()
def create_category():
    business_id = int(get_jwt_identity())
    data = request.get_json()
    last_category = Category.query.filter_by(
        business_id=business_id
    ).order_by(Category.display_order.desc()).first()

    next_order = (
        last_category.display_order + 1
        if last_category
        else 1
    )
    category = Category(
        name=data["name"],
        image_url=data.get("image_url"),
        business_id=business_id,
        parent_id=data.get("parent_id"),
        display_order=next_order
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({"id": category.id, "name": category.name, "emoji": category.emoji, "image_url": category.image_url}), 201

@categories_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_category(id):
    business_id = int(get_jwt_identity())
    category = Category.query.filter_by(id=id, business_id=business_id).first_or_404()
    data = request.get_json()
    category.name = data.get("name", category.name)
    category.emoji = data.get("emoji", category.emoji)
    category.image_url = data.get("image_url", category.image_url)
    if "parent_id" in data:
        category.parent_id = data["parent_id"]
    db.session.commit()
    return jsonify({"id": category.id, "name": category.name, "emoji": category.emoji, "image_url": category.image_url})

@categories_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_category(id):
    business_id = int(get_jwt_identity())
    category = Category.query.filter_by(id=id, business_id=business_id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Categoría eliminada"})


@categories_bp.route("/<int:id>/move-up", methods=["PUT"])
@jwt_required()
def move_up(id):
    business_id = int(get_jwt_identity())

    category = Category.query.filter_by(
        id=id,
        business_id=business_id
    ).first_or_404()

    previous = Category.query.filter(
        Category.business_id == business_id,
        Category.display_order < category.display_order
    ).order_by(Category.display_order.desc()).first()

    if previous:
        category.display_order, previous.display_order = (
            previous.display_order,
            category.display_order,
        )
        db.session.commit()

    return jsonify({"message": "ok"})

@categories_bp.route("/<int:id>/move-down", methods=["PUT"])
@jwt_required()
def move_down(id):
    business_id = int(get_jwt_identity())

    category = Category.query.filter_by(
        id=id,
        business_id=business_id
    ).first_or_404()

    nxt = Category.query.filter(
        Category.business_id == business_id,
        Category.display_order > category.display_order
    ).order_by(Category.display_order.asc()).first()

    if nxt:
        category.display_order, nxt.display_order = (
            nxt.display_order,
            category.display_order,
        )
        db.session.commit()

    return jsonify({"message": "ok"})


@categories_bp.route("/<int:id>/children", methods=["GET"])
@jwt_required()
def get_children(id):
    business_id = int(get_jwt_identity())

    children = (
        Category.query
        .filter_by(
            business_id=business_id,
            parent_id=id
        )
        .order_by(Category.display_order.asc())
        .all()
    )

    return jsonify([
        {
            "id": c.id,
            "name": c.name,
            "emoji": c.emoji,
            "image_url": c.image_url,
            "display_order": c.display_order
        }
        for c in children
    ])