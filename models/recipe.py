from app import db

class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), unique=True, nullable=False)
    ingredients = db.Column(db.Text)
    procedure = db.Column(db.Text)

    product = db.relationship(
        "Product",
        backref=db.backref("recipe", uselist=False, cascade="all, delete")
    )