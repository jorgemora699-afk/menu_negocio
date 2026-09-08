from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.business import Business
from models.invite_code import InviteCode
from app import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    raw_code = (data.get("invite_code") or "").strip().upper()

    if not raw_code:
        return jsonify({"error": "Ingresa tu código de invitación"}), 400

    invite = InviteCode.query.filter_by(code=raw_code).first()

    if not invite or invite.status != "unused":
        return jsonify({"error": "Código de invitación inválido o ya utilizado"}), 400

    if Business.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email ya registrado"}), 400

    if Business.query.filter_by(slug=data["slug"]).first():
        return jsonify({"error": "Slug ya en uso"}), 400

    business = Business(
        name=data["name"],
        slug=data["slug"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"])
    )
    db.session.add(business)
    db.session.flush()  # asigna business.id antes de vincular el código

    invite.status = "used"
    invite.used_by_business_id = business.id
    invite.used_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"message": "Negocio registrado correctamente"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    business = Business.query.filter_by(email=data["email"]).first()

    if not business or not check_password_hash(business.password_hash, data["password"]):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    token = create_access_token(identity=str(business.id))
    return jsonify({
        "token": token,
        "business": {
            "id": business.id,
            "name": business.name,
            "slug": business.slug,
            "recipes_enabled": business.recipes_enabled,
            "horario_enabled": business.horario_enabled
        }
    }), 200


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    business_id = int(get_jwt_identity())
    business = Business.query.get_or_404(business_id)
    data = request.get_json()

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not check_password_hash(business.password_hash, current_password):
        return jsonify({"error": "La contraseña actual es incorrecta"}), 401

    if len(new_password) < 6:
        return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres"}), 400

    if check_password_hash(business.password_hash, new_password):
        return jsonify({"error": "La nueva contraseña debe ser distinta a la actual"}), 400

    business.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "Contraseña actualizada correctamente"}), 200

@auth_bp.route("/change-pin", methods=["PUT"])
@jwt_required()
def change_pin():
    business_id = int(get_jwt_identity())
    business = Business.query.get_or_404(business_id)

    data = request.get_json()

    current_pin = str(data.get("current_pin", "")).strip()
    new_pin = str(data.get("new_pin", "")).strip()

    if business.recipe_pin != current_pin:
        return jsonify({"error": "El PIN actual es incorrecto"}), 401

    if len(new_pin) != 4 or not new_pin.isdigit():
        return jsonify({"error": "El nuevo PIN debe tener exactamente 4 dígitos"}), 400

    if current_pin == new_pin:
        return jsonify({"error": "El nuevo PIN debe ser diferente al actual"}), 400

    business.recipe_pin = new_pin

    db.session.commit()

    return jsonify({"message": "PIN actualizado correctamente"}), 200