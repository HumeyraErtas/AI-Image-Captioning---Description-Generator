import os
import uuid
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from .config import UPLOAD_FOLDER
from .database import SessionLocal, init_db
from .models import Caption
from .caption_service import generate_captions

# Flask app
app = Flask(__name__)
CORS(app)  # Streamlit'ten gelen istekler için CORS

# Upload klasörünü oluştur
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.before_first_request
def setup():
    """İlk istekte DB tablolarını oluştur."""
    init_db()


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "AI Image Captioning API is running"})


@app.route("/api/caption", methods=["POST"])
def caption_image():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Dosya uzantısı
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        return jsonify({"error": "Unsupported file type"}), 400

    # Benzersiz dosya adı oluştur
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Dosyayı diske kaydet
    file_bytes = file.read()
    with open(filepath, "wb") as f:
        f.write(file_bytes)

    # Caption üret
    try:
        short_caption, long_caption, confidence = generate_captions(file_bytes)
    except Exception as e:
        # Hata durumunda dosyayı silmek de mantıklı olabilir.
        print("Caption error:", e)
        return jsonify({"error": "Failed to generate caption", "details": str(e)}), 500

    # DB'ye kaydet
    db = SessionLocal()
    try:
        caption = Caption(
            image_filename=filename,
            short_caption=short_caption,
            long_caption=long_caption,
            confidence=confidence,
        )
        db.add(caption)
        db.commit()
        db.refresh(caption)
    finally:
        db.close()

    return jsonify({
        "id": caption.id,
        "image_filename": filename,
        "image_url": f"/images/{filename}",
        "short_caption": short_caption,
        "long_caption": long_caption,
        "confidence": confidence,
        "created_at": caption.created_at.isoformat() + "Z"
    })


@app.route("/api/history", methods=["GET"])
def get_history():
    limit = request.args.get("limit", default=20, type=int)

    db = SessionLocal()
    try:
        items = (
            db.query(Caption)
            .order_by(Caption.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()

    data = []
    for c in items:
        data.append({
            "id": c.id,
            "image_filename": c.image_filename,
            "image_url": f"/images/{c.image_filename}",
            "short_caption": c.short_caption,
            "long_caption": c.long_caption,
            "confidence": c.confidence,
            "created_at": c.created_at.isoformat() + "Z"
        })

    return jsonify({"items": data})


@app.route("/images/<path:filename>", methods=["GET"])
def serve_image(filename):
    """Yüklenen görselleri servis eder."""
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    # Geliştirme için:
    app.run(host="0.0.0.0", port=5000, debug=True)
