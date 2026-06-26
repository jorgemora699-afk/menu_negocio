from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import cloudinary
import cloudinary.uploader
import os

uploads_bp = Blueprint("uploads", __name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

@uploads_bp.route("/image", methods=["POST"])
@jwt_required()
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Archivo vacío"}), 400

    result = cloudinary.uploader.upload(file, folder="qrmenu")

    return jsonify({"url": result["secure_url"]}), 200