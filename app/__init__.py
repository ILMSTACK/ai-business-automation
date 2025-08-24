import os
from flask import Flask
from flask_restx import Api

from .config import Config
from . import models  # noqa: F401  (ensure models are imported for migrations)
from .extensions import db, migrate
from flask_cors import CORS
from .routes.home_routes import home_bp
from .routes.llm_routes import llm_bp
from .routes.ml_routes import ml_bp

# RESTX Namespaces
from .routes.business_automation_routes import api as business_automation_api
from .routes.csv_routes import api as csv_api  # <-- RESTX namespace (for Swagger)


def create_app():
    app = Flask(__name__, template_folder="views/templates")
    app.config.from_object(Config)
    CORS(app)

    # Ensure upload folder exists (for CSV storage)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Init DB & migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Register existing blueprints (non-RESTX)
    app.register_blueprint(home_bp)
    app.register_blueprint(llm_bp, url_prefix="/api/llm")
    app.register_blueprint(ml_bp, url_prefix="/api/ml")

    # Initialize Flask-RESTX API (Swagger @ /docs/)
    api = Api(
        app,
        version="1.0",
        title="Business Automation API",
        description="API for automated test case and task generation from user stories",
        doc="/docs/",
    )

    # Register RESTX namespaces (show up in Swagger)
    api.add_namespace(business_automation_api, path="/business-automation")
    api.add_namespace(csv_api, path="/csv")  # templates/upload/status/dashboard/insight

    return app
