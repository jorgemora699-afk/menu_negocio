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
    primary_color = db.Column(db.String(7), default="#222222")
    secondary_color = db.Column(db.String(7), default="#ffffff")

    categories = db.relationship("Category", backref="business", lazy=True, cascade="all, delete")