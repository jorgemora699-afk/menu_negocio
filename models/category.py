from app import db

class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    emoji = db.Column(db.String(10), default="🍽")
    image_url = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0)

    business_id = db.Column(
        db.Integer,
        db.ForeignKey("businesses.id"),
        nullable=False
    )

    products = db.relationship(
        "Product",
        backref="category",
        lazy=True,
        cascade="all, delete"
    )