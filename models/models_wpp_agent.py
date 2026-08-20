from app import db
from sqlalchemy import Numeric
from datetime import datetime


class BusinessWhatsAppConfig(db.Model):
    __tablename__ = "business_whatsapp_config"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(
        db.Integer,
        db.ForeignKey("businesses.id"),
        nullable=False,
        unique=True
    )
    phone_number_id = db.Column(db.String(50), nullable=False, unique=True)   # ID del número en Meta
    whatsapp_business_number = db.Column(db.String(20), nullable=False)       # número visible, para notificar al dueño
    access_token = db.Column(db.String(500), nullable=False)                  # token de Meta (o referencia a secret manager)
    active = db.Column(db.Boolean, default=True)

    business = db.relationship("Business", backref="whatsapp_config", uselist=False)


class ConversationHistory(db.Model):
    __tablename__ = "conversation_history"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), nullable=False)   # 'user' | 'assistant' | 'tool'
    content = db.Column(db.Text, nullable=False)       # texto o JSON serializado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    business = db.relationship("Business", backref="conversation_history")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    items = db.Column(db.JSON, nullable=False)         # [{product_id, name, quantity, unit_price, notes}]
    total = db.Column(Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default="pendiente_aprobacion")
    # valores posibles: 'pendiente_aprobacion' | 'aprobado' | 'rechazado' | 'entregado' | 'cancelado'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)

    business = db.relationship("Business", backref="orders")