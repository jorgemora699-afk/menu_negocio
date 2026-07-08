from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models.business import Business
from app import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
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
    return jsonify({"token": token, "business": {"id": business.id, "name": business.name, "slug": business.slug}}), 200
    data = request.get_json()

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
    db.session.commit()

    return jsonify({"message": "Negocio registrado correctamente"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    business = Business.query.filter_by(email=data["email"]).first()

    if not business or not check_password_hash(business.password_hash, data["password"]):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    token = create_access_token(identity=str(business.id))
    return jsonify({"token": token, "business": {"id": business.id, "name": business.name, "slug": business.slug}}), 200