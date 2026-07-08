from datetime import datetime
from app import db


class InviteCode(db.Model):
    __tablename__ = "invite_codes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)

    # Nota tuya para recordar a quién se lo diste (ej: "Café Aroma - WhatsApp 15/07")
    label = db.Column(db.String(120))

    # unused | used | revoked
    status = db.Column(db.String(20), default="unused", nullable=False)

    used_by_business_id = db.Column(
        db.Integer, db.ForeignKey("businesses.id"), nullable=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)

    used_by_business = db.relationship("Business", backref="invite_code_used", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "label": self.label,
            "status": self.status,
            "used_by_business_id": self.used_by_business_id,
            "used_by_business_name": self.used_by_business.name if self.used_by_business else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "used_at": self.used_at.isoformat() if self.used_at else None,
        }