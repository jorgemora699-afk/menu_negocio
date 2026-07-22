from app import db
from sqlalchemy import Numeric

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(255))
    available = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )