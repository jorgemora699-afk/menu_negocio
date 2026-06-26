from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.category import Category
from app import db

categories_bp = Blueprint("categories", __name__)

@categories_bp.route("/", methods=["GET"])
@jwt_required()
def get_categories():
    business_id = get_jwt_identity()
    categories = Category.query.filter_by(business_id=business_id).all()
    return jsonify([{"id": c.id, "name": c.name, "emoji": c.emoji} for c in categories])

@categories_bp.route("/", methods=["POST"])
@jwt_required()
def create_category():
    business_id = get_jwt_identity()
    data = request.get_json()
    category = Category(name=data["name"], emoji=data.get("emoji", "🍽"), business_id=business_id)
    db.session.add(category)
    db.session.commit()
    return jsonify({"id": category.id, "name": category.name, "emoji": category.emoji}), 201

@categories_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_category(id):
    business_id = get_jwt_identity()
    category = Category.query.filter_by(id=id, business_id=business_id).first_or_404()
    data = request.get_json()
    category.name = data.get("name", category.name)
    category.emoji = data.get("emoji", category.emoji)
    db.session.commit()
    return jsonify({"id": category.id, "name": category.name, "emoji": category.emoji})

@categories_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_category(id):
    business_id = get_jwt_identity()
    category = Category.query.filter_by(id=id, business_id=business_id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Categoría eliminada"})