"""
services/salario_service.py

Cálculo de horas trabajadas y salario para el sistema de horario de Arte Frío.
Tarifa diferenciada: entre semana vs fin de semana, según el día en que
empezó el turno.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

ZONA_COLOMBIA = ZoneInfo("America/Bogota")
ZONA_UTC = ZoneInfo("UTC")

TARIFA_ENTRE_SEMANA = 10000
TARIFA_FIN_DE_SEMANA = 12000

# lunes=0 ... domingo=6 -> sábado(5) y domingo(6) son fin de semana
DIAS_FIN_DE_SEMANA = {5, 6}


def hoy_colombia():
    """Fecha de 'hoy' según la hora de Colombia, sin importar en qué
    zona horaria esté corriendo el servidor."""
    return datetime.now(ZONA_COLOMBIA).date()


def hora_local_a_utc(fecha, hora_str):
    """Convierte 'HH:MM' (hora de Colombia, en la fecha del turno) a un
    datetime naive en UTC, listo para guardar."""
    try:
        hh, mm = map(int, hora_str.split(":"))
    except (ValueError, AttributeError):
        raise ValueError("Formato de hora inválido, usa HH:MM")

    local_dt = datetime.combine(fecha, time(hour=hh, minute=mm), tzinfo=ZONA_COLOMBIA)
    return local_dt.astimezone(ZONA_UTC).replace(tzinfo=None)


def calcular_horas_trabajadas(hora_entrada, hora_salida):
    """Recibe dos datetime y devuelve las horas trabajadas, redondeadas a 2 decimales."""
    if hora_entrada is None or hora_salida is None:
        return None
    delta = hora_salida - hora_entrada
    return round(delta.total_seconds() / 3600, 2)


def tarifa_para_fecha(fecha):
    """Devuelve la tarifa por hora según el día de la semana (usa el día
    en que empezó el turno)."""
    if fecha.weekday() in DIAS_FIN_DE_SEMANA:
        return TARIFA_FIN_DE_SEMANA
    return TARIFA_ENTRE_SEMANA


def calcular_salario_turno(turno):
    """Calcula el salario de un turno individual ya cerrado (con hora_salida)."""
    horas = calcular_horas_trabajadas(turno.hora_entrada, turno.hora_salida)
    if horas is None:
        return None
    tarifa = tarifa_para_fecha(turno.fecha)
    return round(horas * tarifa, 2)


def calcular_salario_empleado(empleado, turnos):
    """
    turnos: lista de objetos Turno (ya cerrados) de ese empleado en el período.
    Devuelve un resumen con horas totales y salario total, respetando la
    tarifa distinta de cada turno según su día.
    """
    total_horas = 0
    total_salario = 0

    for turno in turnos:
        horas = calcular_horas_trabajadas(turno.hora_entrada, turno.hora_salida)
        if horas is None:
            continue
        tarifa = tarifa_para_fecha(turno.fecha)
        total_horas += horas
        total_salario += horas * tarifa

    return {
        "empleado_id": empleado.id,
        "empleado_nombre": empleado.nombre,
        "total_horas": round(total_horas, 2),
        "total_salario": round(total_salario, 2),
    }