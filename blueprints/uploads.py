from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import cloudinary
import cloudinary.uploader
import cloudinary.exceptions
import os

uploads_bp = Blueprint("uploads", __name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_MIMETYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


def is_allowed_file(filename, mimetype):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS and mimetype in ALLOWED_MIMETYPES


@uploads_bp.route("/image", methods=["POST"])
@jwt_required()
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Archivo vacío"}), 400

    if not is_allowed_file(file.filename, file.mimetype):
        return jsonify({"error": "Solo se permiten imágenes (PNG, JPG, WEBP, GIF)"}), 400

    try:
        result = cloudinary.uploader.upload(
            file,
            folder="qrmenu",
            resource_type="image",              # rechaza videos, PDFs, archivos raw, etc.
            allowed_formats=["png", "jpg", "jpeg", "webp", "gif"],
            max_file_size=5_000_000              # ~5MB, ajusta según necesites
        )
    except cloudinary.exceptions.Error as e:
        return jsonify({"error": "No se pudo procesar la imagen"}), 400
    except Exception as e:
        return jsonify({"error": "Error al subir la imagen"}), 500

    return jsonify({"url": result["secure_url"]}), 200