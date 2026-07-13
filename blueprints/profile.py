from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.business import Business
from app import db

profile_bp = Blueprint("profile", __name__)

VALID_FONT_KEYS = {"editorial", "clasico", "moderno", "calido", "minimal"}

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
        "banner_url": business.banner_url,
        "tagline": business.tagline,
        "accent_color": business.accent_color,
        "background_color": business.background_color,
        "text_color": business.text_color,
        "font_key": business.font_key,
        "recipes_enabled": business.recipes_enabled,
    })

@profile_bp.route("/", methods=["PUT"])
@jwt_required()
def update_profile():
    business_id = int(get_jwt_identity())
    business = Business.query.get_or_404(business_id)
    data = request.get_json()

    business.name = data.get("name", business.name)
    business.logo_url = data.get("logo_url", business.logo_url)
    business.banner_url = data.get("banner_url", business.banner_url)
    business.tagline = data.get("tagline", business.tagline)

    accent = data.get("accent_color")
    if accent:
        business.accent_color = accent

    background = data.get("background_color")
    if background:
        business.background_color = background

    text = data.get("text_color")
    if text:
        business.text_color = text

    font_key = data.get("font_key")
    if font_key and font_key in VALID_FONT_KEYS:
        business.font_key = font_key

    db.session.commit()

    return jsonify({"message": "Perfil actualizado correctamente"})