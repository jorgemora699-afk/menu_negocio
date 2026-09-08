from app import db


class Turno(db.Model):
    __tablename__ = "turnos"

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.DateTime, nullable=False)
    hora_salida = db.Column(db.DateTime, nullable=True)

    empleado = db.relationship("Empleado", backref="turnos")