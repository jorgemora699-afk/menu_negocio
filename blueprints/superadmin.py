import os
import secrets
from flask import Blueprint, request, jsonify, abort
from werkzeug.security import generate_password_hash
from models.invite_code import InviteCode
from models.business import Business
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


# ---------------------------------------------------------------------------
# Negocios: listar, restablecer contraseña manualmente, asignar color de fondo
# ---------------------------------------------------------------------------

def business_to_dict(b):
    return {
        "id": b.id,
        "name": b.name,
        "slug": b.slug,
        "email": b.email,
    }


@superadmin_bp.route("/businesses", methods=["GET"])
def list_businesses():
    require_superadmin()

    search = request.args.get("q", "").strip().lower()

    query = Business.query
    if search:
        query = query.filter(
            db.or_(
                Business.name.ilike(f"%{search}%"),
                Business.email.ilike(f"%{search}%"),
                Business.slug.ilike(f"%{search}%"),
            )
        )

    businesses = query.order_by(Business.name.asc()).all()
    return jsonify([business_to_dict(b) for b in businesses]), 200


@superadmin_bp.route("/businesses/<int:business_id>/reset-password", methods=["POST"])
def reset_business_password(business_id):
    require_superadmin()

    business = Business.query.get_or_404(business_id)

    # Contraseña temporal fácil de dictar/copiar por WhatsApp (10 caracteres, sin ambigüedades)
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin O/0, I/1/L para evitar confusiones
    new_password = "".join(secrets.choice(alphabet) for _ in range(10))

    business.password_hash = generate_password_hash(new_password)
    db.session.commit()

    # La contraseña en texto plano solo se devuelve UNA VEZ, aquí.
    # No queda guardada en ningún lado — cópiala y mándasela al negocio ya mismo.
    return jsonify({
        "id": business.id,
        "email": business.email,
        "new_password": new_password
    }), 200