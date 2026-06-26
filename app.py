from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        from models.business import Business
        from models.category import Category
        from models.product import Product
        db.create_all()

        from blueprints.auth import auth_bp
        from blueprints.categories import categories_bp
        from blueprints.products import products_bp

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        app.register_blueprint(categories_bp, url_prefix="/api/categories")
        app.register_blueprint(products_bp, url_prefix="/api/products")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))