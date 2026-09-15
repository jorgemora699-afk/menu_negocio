from app import db
from sqlalchemy import Numeric


class Empleado(db.Model):
    __tablename__ = "empleados"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    # Tarifa personalizada (opcional). Si quedan en None, se usa la tarifa
    # global del negocio (ver services/salario_service.py).
    valor_hora_semana = db.Column(Numeric(10, 2), nullable=True)
    valor_hora_fin_semana = db.Column(Numeric(10, 2), nullable=True)

    business = db.relationship("Business", backref="empleados")