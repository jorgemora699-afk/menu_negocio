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
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8MB máximo por request

    CORS(app)
    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        from models.business import Business
        from models.category import Category
        from models.product import Product
        from models.invite_code import InviteCode 
        from models.recipe import Recipe
        from models.models_wpp_agent import BusinessWhatsAppConfig, ConversationHistory, Order
        db.create_all()

        from blueprints.auth import auth_bp
        from blueprints.categories import categories_bp
        from blueprints.products import products_bp
        from blueprints.menu import menu_bp
        from blueprints.profile import profile_bp
        from blueprints.uploads import uploads_bp
        from blueprints.superadmin import superadmin_bp
        from blueprints.recipes import recipes_bp
        from blueprints.whatsapp_webhook import whatsapp_webhook_bp

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        app.register_blueprint(categories_bp, url_prefix="/api/categories")
        app.register_blueprint(products_bp, url_prefix="/api/products")
        app.register_blueprint(menu_bp, url_prefix="/api/menu")
        app.register_blueprint(profile_bp, url_prefix="/api/profile")
        app.register_blueprint(uploads_bp, url_prefix="/api/uploads")
        app.register_blueprint(superadmin_bp, url_prefix="/api/superadmin")
        app.register_blueprint(recipes_bp, url_prefix="/api/recipes")
        app.register_blueprint(whatsapp_webhook_bp, url_prefix="/api")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))