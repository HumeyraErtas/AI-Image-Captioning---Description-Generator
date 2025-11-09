import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite veritabanı yolu
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'captions.db'}"
)

# Yüklenen görsellerin kaydedildiği klasör
UPLOAD_FOLDER = os.getenv(
    "UPLOAD_FOLDER",
    str(BASE_DIR / "uploads")
)

# API'nin dışarıya açık temel URL'si (Streamlit buna istek yollayacak)
# Geliştirme aşamasında Flask için:
#   host=0.0.0.0, port=5000 -> http://localhost:5000
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
