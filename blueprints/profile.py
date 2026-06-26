from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.business import Business
from app import db

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/", methods=["GET"])
@jwt_required()
def get_profile():
    business_id = int(get_jwt_identity())
    business = Business.query.get_or_404(business_id)
    return jsonify({
        "id": business.id,
        "name": business.name,
        "slug": business.slug,
        "email": business.email,
        "logo_url": business.logo_url,
        "tagline": business.tagline,
        "primary_color": business.primary_color,
        "secondary_color": business.secondary_color
    })

@profile_bp.route("/", methods=["PUT"])
@jwt_required()
def update_profile():
    business_id = int(get_jwt_identity())
    business = Business.query.get_or_404(business_id)
    data = request.get_json()

    business.name = data.get("name", business.name)
    business.logo_url = data.get("logo_url", business.logo_url)
    business.tagline = data.get("tagline", business.tagline)
    business.primary_color = data.get("primary_color", business.primary_color)
    business.secondary_color = data.get("secondary_color", business.secondary_color)

    db.session.commit()

    return jsonify({"message": "Perfil actualizado correctamente"})