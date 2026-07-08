import os
import secrets
from flask import Blueprint, request, jsonify, abort
from models.invite_code import InviteCode
from app import db

superadmin_bp = Blueprint("superadmin", __name__)

# Define SUPERADMIN_KEY en tus variables de entorno (Railway > Variables).
# Ejemplo para generar una clave fuerte localmente:
#   python -c "import secrets; print(secrets.token_hex(24))"
SUPERADMIN_KEY = os.environ.get("SUPERADMIN_KEY")


def require_superadmin():
    key = request.headers.get("X-Superadmin-Key")
    if not SUPERADMIN_KEY or key != SUPERADMIN_KEY:
        abort(401, description="No autorizado")


@superadmin_bp.route("/invite-codes", methods=["POST"])
def create_invite_code():
    require_superadmin()

    data = request.get_json(silent=True) or {}
    label = data.get("label", "").strip()

    # Genera un código único de 8 caracteres (hex, fácil de leer y copiar)
    code = secrets.token_hex(4).upper()
    while InviteCode.query.filter_by(code=code).first():
        code = secrets.token_hex(4).upper()

    invite = InviteCode(code=code, label=label)
    db.session.add(invite)
    db.session.commit()

    return jsonify(invite.to_dict()), 201


@superadmin_bp.route("/invite-codes", methods=["GET"])
def list_invite_codes():
    require_superadmin()

    codes = InviteCode.query.order_by(InviteCode.created_at.desc()).all()
    return jsonify([c.to_dict() for c in codes]), 200


@superadmin_bp.route("/invite-codes/<int:code_id>/revoke", methods=["PATCH"])
def revoke_invite_code(code_id):
    require_superadmin()

    invite = InviteCode.query.get_or_404(code_id)

    if invite.status == "used":
        return jsonify({"error": "No puedes revocar un código ya utilizado"}), 400

    invite.status = "revoked"
    db.session.commit()

    return jsonify(invite.to_dict()), 200