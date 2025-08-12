from flask import Flask
from .config import Config
from .extensions import db, migrate
from .routes.home_routes import home_bp
from .routes.llm_routes import llm_bp
from .routes.ml_routes import ml_bp

def create_app():
    app = Flask(__name__, template_folder="views/templates")
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(llm_bp, url_prefix="/api/llm")
    app.register_blueprint(ml_bp, url_prefix="/api/ml")

    return app
