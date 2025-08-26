import os
from dotenv import load_dotenv
load_dotenv()

# base dir for composing paths (…/app/.. -> project root)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class Config:
    # --- Database (Supabase PostgreSQL) ---
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SUPABASE_DATABASE_URL")
        or "postgresql://postgres.[your-project-ref]:[your-password]@aws-0-[region].pooler.supabase.com:5432/postgres"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # --- App secrets / models ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    # --- CSV uploads (sales/inventory) ---
    # Files will be saved to: public/storage/<user_id>/<upload_id>-<type>.csv
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        os.path.join(BASE_DIR, "public", "storage")
    )
    # hard limit for CSV rows (hackathon-friendly)
    MAX_CSV_ROWS = int(os.getenv("MAX_CSV_ROWS", "100"))
    # hard limit for upload size (in MB; default 5MB)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "5")) * 1024 * 1024

    # --- Swagger/RESTX (optional niceties) ---
    RESTX_MASK_SWAGGER = False  # show all fields in docs
