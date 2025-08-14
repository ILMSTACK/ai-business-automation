import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Supabase PostgreSQL connection
    SQLALCHEMY_DATABASE_URI = os.environ.get('SUPABASE_DATABASE_URL') or \
                              'postgresql://postgres.[your-project-ref]:[your-password]@aws-0-[region].pooler.supabase.com:5432/postgres'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pooling for better performance with Supabase
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
