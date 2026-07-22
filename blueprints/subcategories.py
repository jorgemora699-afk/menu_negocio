from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models.category import Category
from models.subcategory import Subcategory

subcategories_bp = Blueprint("subcategories", __name__)


@subcategories_bp.route("/", methods=["GET"])
@jwt_required()
def get_subcategories():
    business_id = int(get_jwt_identity())
    category_id = request.args.get("category_id")

    if not category_id:
        return jsonify({"error": "category_id es obligatorio"}), 400

    category = Category.query.filter_by(
        id=category_id,
        business_id=business_id
    ).first_or_404()

    subcategories = (
        Subcategory.query
        .filter_by(category_id=category.id)
        .order_by(Subcategory.display_order.asc())
        .all()
    )

    return jsonify([
        {
            "id": s.id,
            "name": s.name,
            "display_order": s.display_order
        }
        for s in subcategories
    ])


@subcategories_bp.route("/", methods=["POST"])
@jwt_required()
def create_subcategory():
    business_id = int(get_jwt_identity())
    data = request.get_json()

    category = Category.query.filter_by(
        id=data["category_id"],
        business_id=business_id
    ).first_or_404()

    last = (
        Subcategory.query
        .filter_by(category_id=category.id)
        .order_by(Subcategory.display_order.desc())
        .first()
    )

    next_order = last.display_order + 1 if last else 1

    subcategory = Subcategory(
        name=data["name"],
        category_id=category.id,
        display_order=next_order
    )

    db.session.add(subcategory)
    db.session.commit()

    return jsonify({
        "id": subcategory.id,
        "name": subcategory.name
    }), 201


@subcategories_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_subcategory(id):
    business_id = int(get_jwt_identity())

    subcategory = (
        Subcategory.query
        .join(Category)
        .filter(
            Subcategory.id == id,
            Category.business_id == business_id
        )
        .first_or_404()
    )

    data = request.get_json()

    subcategory.name = data.get("name", subcategory.name)

    db.session.commit()

    return jsonify({
        "id": subcategory.id,
        "name": subcategory.name
    })


@subcategories_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_subcategory(id):
    business_id = int(get_jwt_identity())

    subcategory = (
        Subcategory.query
        .join(Category)
        .filter(
            Subcategory.id == id,
            Category.business_id == business_id
        )
        .first_or_404()
    )

    db.session.delete(subcategory)
    db.session.commit()

    return jsonify({
        "message": "Subcategoría eliminada"
    })


@subcategories_bp.route("/<int:id>/move-up", methods=["PUT"])
@jwt_required()
def move_up(id):
    business_id = int(get_jwt_identity())

    subcategory = (
        Subcategory.query
        .join(Category)
        .filter(
            Subcategory.id == id,
            Category.business_id == business_id
        )
        .first_or_404()
    )

    previous = (
        Subcategory.query
        .filter(
            Subcategory.category_id == subcategory.category_id,
            Subcategory.display_order < subcategory.display_order
        )
        .order_by(Subcategory.display_order.desc())
        .first()
    )

    if previous:
        subcategory.display_order, previous.display_order = (
            previous.display_order,
            subcategory.display_order
        )
        db.session.commit()

    return jsonify({"message": "ok"})


@subcategories_bp.route("/<int:id>/move-down", methods=["PUT"])
@jwt_required()
def move_down(id):
    business_id = int(get_jwt_identity())

    subcategory = (
        Subcategory.query
        .join(Category)
        .filter(
            Subcategory.id == id,
            Category.business_id == business_id
        )
        .first_or_404()
    )

    nxt = (
        Subcategory.query
        .filter(
            Subcategory.category_id == subcategory.category_id,
            Subcategory.display_order > subcategory.display_order
        )
        .order_by(Subcategory.display_order.asc())
        .first()
    )

    if nxt:
        subcategory.display_order, nxt.display_order = (
            nxt.display_order,
            subcategory.display_order
        )
        db.session.commit()

    return jsonify({"message": "ok"})