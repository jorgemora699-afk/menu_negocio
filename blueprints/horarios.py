"""
blueprints/horarios.py

Endpoints relacionados con el registro de horario de empleados.
- verificar-pin: valida el PIN compartido y emite un JWT temporal con rol 'empleado'
- empleados: lista los empleados activos del negocio (para elegir "quién eres")
- entrada / salida: marcan el turno del empleado seleccionado
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt

from app import db
from models.business import Business
from models.empleado import Empleado
from models.turno import Turno
from services.salario_service import hoy_colombia

horarios_bp = Blueprint("horarios", __name__)


def _business_id_empleado():
    """Extrae el business_id del JWT temporal de empleado y valida el rol."""
    claims = get_jwt()
    if claims.get("role") != "empleado":
        return None
    return claims.get("business_id")


@horarios_bp.route("/verificar-pin", methods=["POST"])
def verificar_pin():
    data = request.get_json(silent=True) or {}
    slug = data.get("slug")
    pin = data.get("pin")

    if not slug or not pin:
        return jsonify({"error": "Faltan datos: slug y pin son requeridos"}), 400

    business = Business.query.filter_by(slug=slug).first()

    if not business or not business.horario_enabled:
        return jsonify({"error": "Esta función no está disponible para este negocio"}), 404

    if not business.horario_pin or business.horario_pin != pin:
        return jsonify({"error": "PIN incorrecto"}), 401

    access_token = create_access_token(
        identity=f"empleado-business-{business.id}",
        additional_claims={"business_id": business.id, "role": "empleado"},
    )

    return jsonify({
        "access_token": access_token,
        "business_id": business.id,
        "business_name": business.name,
    }), 200


@horarios_bp.route("/empleados", methods=["GET"])
@jwt_required()
def listar_empleados_activos():
    business_id = _business_id_empleado()
    if business_id is None:
        return jsonify({"error": "No autorizado"}), 403

    empleados = Empleado.query.filter_by(business_id=business_id, activo=True).order_by(Empleado.nombre.asc()).all()
    return jsonify([{"id": e.id, "nombre": e.nombre} for e in empleados])


@horarios_bp.route("/entrada", methods=["POST"])
@jwt_required()
def marcar_entrada():
    business_id = _business_id_empleado()
    if business_id is None:
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json(silent=True) or {}
    empleado_id = data.get("empleado_id")

    empleado = Empleado.query.filter_by(id=empleado_id, business_id=business_id, activo=True).first()
    if not empleado:
        return jsonify({"error": "Empleado no encontrado"}), 404

    hoy = hoy_colombia()

    turno_abierto = Turno.query.filter_by(empleado_id=empleado.id, hora_salida=None).first()
    if turno_abierto:
        return jsonify({"error": "Ya hay una entrada registrada sin salida marcada"}), 400

    turno = Turno(
        empleado_id=empleado.id,
        fecha=hoy,
        hora_entrada=datetime.utcnow(),
    )
    db.session.add(turno)
    db.session.commit()

    return jsonify({"message": "Entrada registrada", "turno_id": turno.id}), 201


@horarios_bp.route("/salida", methods=["POST"])
@jwt_required()
def marcar_salida():
    business_id = _business_id_empleado()
    if business_id is None:
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json(silent=True) or {}
    empleado_id = data.get("empleado_id")

    empleado = Empleado.query.filter_by(id=empleado_id, business_id=business_id, activo=True).first()
    if not empleado:
        return jsonify({"error": "Empleado no encontrado"}), 404

    turno = Turno.query.filter_by(
        empleado_id=empleado.id, hora_salida=None
    ).order_by(Turno.fecha.desc()).first()

    if not turno:
        return jsonify({"error": "No hay una entrada abierta para marcar salida"}), 400

    turno.hora_salida = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Salida registrada", "turno_id": turno.id}), 200