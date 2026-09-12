import io
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from models.empleado import Empleado
from models.turno import Turno
from models.business import Business
from services.salario_service import (
    calcular_salario_empleado,
    calcular_horas_trabajadas,
    hora_local_a_utc,
    tarifa_para_fecha,
)
from services.pdf_service import generar_pdf_salario, generar_pdf_reporte_general

empleados_bp = Blueprint("empleados", __name__)


def _parsear_rango_fechas():
    desde_str = request.args.get("desde")
    hasta_str = request.args.get("hasta")

    if not desde_str or not hasta_str:
        return None, None, "Debes indicar 'desde' y 'hasta' (YYYY-MM-DD)"

    try:
        desde = datetime.strptime(desde_str, "%Y-%m-%d").date()
        hasta = datetime.strptime(hasta_str, "%Y-%m-%d").date()
    except ValueError:
        return None, None, "Formato de fecha inválido, usa YYYY-MM-DD"

    return desde, hasta, None


@empleados_bp.route("/", methods=["GET"])
@jwt_required()
def get_empleados():
    business_id = int(get_jwt_identity())
    empleados = Empleado.query.filter_by(business_id=business_id).order_by(Empleado.nombre.asc()).all()
    return jsonify([{
        "id": e.id,
        "nombre": e.nombre,
        "activo": e.activo,
    } for e in empleados])


@empleados_bp.route("/", methods=["POST"])
@jwt_required()
def create_empleado():
    business_id = int(get_jwt_identity())
    data = request.get_json()

    empleado = Empleado(
        business_id=business_id,
        nombre=data["nombre"],
        activo=data.get("activo", True),
    )
    db.session.add(empleado)
    db.session.commit()
    return jsonify({"id": empleado.id, "nombre": empleado.nombre}), 201


@empleados_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_empleado(id):
    business_id = int(get_jwt_identity())
    empleado = Empleado.query.filter_by(id=id, business_id=business_id).first_or_404()
    data = request.get_json()

    empleado.nombre = data.get("nombre", empleado.nombre)
    empleado.activo = data.get("activo", empleado.activo)
    db.session.commit()
    return jsonify({"id": empleado.id, "nombre": empleado.nombre})


@empleados_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_empleado(id):
    business_id = int(get_jwt_identity())
    empleado = Empleado.query.filter_by(id=id, business_id=business_id).first_or_404()
    db.session.delete(empleado)
    db.session.commit()
    return jsonify({"message": "Empleado eliminado"})


@empleados_bp.route("/salarios", methods=["GET"])
@jwt_required()
def calcular_salarios():
    """
    Calcula el salario de cada empleado activo en un rango de fechas,
    según las horas trabajadas y la tarifa entre semana/fin de semana.

    Query params: ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    """
    business_id = int(get_jwt_identity())

    desde, hasta, error = _parsear_rango_fechas()
    if error:
        return jsonify({"error": error}), 400

    empleados = Empleado.query.filter_by(business_id=business_id, activo=True).order_by(Empleado.nombre.asc()).all()

    resultados = []
    for empleado in empleados:
        turnos = Turno.query.filter(
            Turno.empleado_id == empleado.id,
            Turno.fecha.between(desde, hasta),
            Turno.hora_salida.isnot(None),
        ).all()

        resumen = calcular_salario_empleado(empleado, turnos)
        resultados.append(resumen)

    total_general = round(sum(r["total_salario"] for r in resultados), 2)

    return jsonify({
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "empleados": resultados,
        "total_general": total_general,
    })


@empleados_bp.route("/<int:id>/turnos", methods=["GET"])
@jwt_required()
def listar_turnos_empleado(id):
    """
    Detalle día por día de los turnos de un empleado en un rango de fechas,
    incluyendo turnos abiertos (sin hora_salida aún).

    Query params: ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    """
    business_id = int(get_jwt_identity())
    empleado = Empleado.query.filter_by(id=id, business_id=business_id).first_or_404()

    desde, hasta, error = _parsear_rango_fechas()
    if error:
        return jsonify({"error": error}), 400

    turnos = Turno.query.filter(
        Turno.empleado_id == empleado.id,
        Turno.fecha.between(desde, hasta),
    ).order_by(Turno.fecha.desc()).all()

    return jsonify([{
        "id": t.id,
        "fecha": t.fecha.isoformat(),
        "hora_entrada": (t.hora_entrada.isoformat() + "Z") if t.hora_entrada else None,
        "hora_salida": (t.hora_salida.isoformat() + "Z") if t.hora_salida else None,
        "horas_trabajadas": calcular_horas_trabajadas(t.hora_entrada, t.hora_salida),
    } for t in turnos])


@empleados_bp.route("/turnos/<int:turno_id>", methods=["PUT"])
@jwt_required()
def actualizar_turno(turno_id):
    """
    Permite al dueño corregir la hora de entrada y/o salida de un turno
    puntual — para arreglar olvidos o errores de marcaje del empleado.
    La fecha del turno no cambia, solo las horas dentro de ese día.

    Body: { "hora_entrada": "HH:MM", "hora_salida": "HH:MM" }  (ambos opcionales)
    """
    business_id = int(get_jwt_identity())

    turno = (
        Turno.query.join(Empleado)
        .filter(Turno.id == turno_id, Empleado.business_id == business_id)
        .first_or_404()
    )

    data = request.get_json(silent=True) or {}

    nueva_entrada = turno.hora_entrada
    nueva_salida = turno.hora_salida

    try:
        if data.get("hora_entrada"):
            nueva_entrada = hora_local_a_utc(turno.fecha, data["hora_entrada"])
        if data.get("hora_salida"):
            nueva_salida = hora_local_a_utc(turno.fecha, data["hora_salida"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if nueva_entrada and nueva_salida and nueva_salida <= nueva_entrada:
        return jsonify({"error": "La hora de salida debe ser posterior a la hora de entrada"}), 400

    turno.hora_entrada = nueva_entrada
    turno.hora_salida = nueva_salida
    db.session.commit()

    return jsonify({
        "id": turno.id,
        "fecha": turno.fecha.isoformat(),
        "hora_entrada": turno.hora_entrada.isoformat() + "Z" if turno.hora_entrada else None,
        "hora_salida": turno.hora_salida.isoformat() + "Z" if turno.hora_salida else None,
        "horas_trabajadas": calcular_horas_trabajadas(turno.hora_entrada, turno.hora_salida),
    })


@empleados_bp.route("/<int:id>/pdf", methods=["GET"])
@jwt_required()
def generar_pdf_empleado(id):
    """
    Genera un PDF con el detalle de horario y salario de un empleado en un
    rango de fechas, listo para descargar y enviarle al empleado.

    Query params: ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    """
    business_id = int(get_jwt_identity())
    empleado = Empleado.query.filter_by(id=id, business_id=business_id).first_or_404()
    business = Business.query.get(business_id)

    desde, hasta, error = _parsear_rango_fechas()
    if error:
        return jsonify({"error": error}), 400

    turnos = Turno.query.filter(
        Turno.empleado_id == empleado.id,
        Turno.fecha.between(desde, hasta),
    ).order_by(Turno.fecha.asc()).all()

    filas = []
    total_horas = 0
    total_salario = 0

    for t in turnos:
        horas = calcular_horas_trabajadas(t.hora_entrada, t.hora_salida)
        tarifa = tarifa_para_fecha(t.fecha)
        subtotal = round(horas * tarifa, 2) if horas is not None else None

        if horas is not None:
            total_horas += horas
            total_salario += subtotal

        filas.append({
            "fecha": t.fecha,
            "hora_entrada": t.hora_entrada,
            "hora_salida": t.hora_salida,
            "horas": horas,
            "tarifa": tarifa,
            "subtotal": subtotal,
        })

    pdf_buffer = generar_pdf_salario(
        business_nombre=business.name,
        empleado_nombre=empleado.nombre,
        desde=desde,
        hasta=hasta,
        filas=filas,
        total_horas=round(total_horas, 2),
        total_salario=round(total_salario, 2),
    )

    nombre_archivo = f"salario_{empleado.nombre.replace(' ', '_')}_{desde.isoformat()}_{hasta.isoformat()}.pdf"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nombre_archivo,
    )


@empleados_bp.route("/reporte-general/pdf", methods=["GET"])
@jwt_required()
def generar_pdf_reporte_general_endpoint():
    """
    Genera un PDF resumen con el salario de todos los empleados activos
    en un rango de fechas, más el total general a pagar.

    Query params: ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    """
    business_id = int(get_jwt_identity())
    business = Business.query.get(business_id)

    desde, hasta, error = _parsear_rango_fechas()
    if error:
        return jsonify({"error": error}), 400

    empleados = Empleado.query.filter_by(business_id=business_id, activo=True).order_by(Empleado.nombre.asc()).all()

    resultados = []
    for empleado in empleados:
        turnos = Turno.query.filter(
            Turno.empleado_id == empleado.id,
            Turno.fecha.between(desde, hasta),
            Turno.hora_salida.isnot(None),
        ).all()
        resultados.append(calcular_salario_empleado(empleado, turnos))

    total_general = round(sum(r["total_salario"] for r in resultados), 2)

    pdf_buffer = generar_pdf_reporte_general(
        business_nombre=business.name,
        desde=desde,
        hasta=hasta,
        empleados=resultados,
        total_general=total_general,
    )

    nombre_archivo = f"reporte_nomina_{desde.isoformat()}_{hasta.isoformat()}.pdf"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nombre_archivo,
    )