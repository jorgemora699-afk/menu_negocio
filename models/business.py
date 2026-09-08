from app import db

class Business(db.Model):
    __tablename__ = "businesses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    logo_url = db.Column(db.String(255))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tagline = db.Column(db.String(255))
    banner_url = db.Column(db.String(255))

    accent_color = db.Column(db.String(7), default="#9c7a3c")
    background_color = db.Column(db.String(7), default="#f7f4ee")
    text_color = db.Column(db.String(7), default="#1b1812")
    font_key = db.Column(db.String(20), default="editorial")
    recipes_enabled = db.Column(db.Boolean, default=False)
    recipe_pin = db.Column(db.String(4))
    horario_enabled = db.Column(db.Boolean, default=False)
    horario_pin = db.Column(db.String(4))

    categories = db.relationship("Category", backref="business", lazy=True, cascade="all, delete")