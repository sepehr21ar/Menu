from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"

STATIC_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./menu_maker.db")

SECRET_KEY = os.getenv("MENU_MAKER_SECRET", "change-this-secret-key")

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

MAX_IMAGE_SIZE = 4 * 1024 * 1024

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
