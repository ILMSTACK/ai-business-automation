from flask import Flask
from flask_restx import Api
from flask_cors import CORS
from .config import Config
from . import models
from .extensions import db, migrate
from .routes.home_routes import home_bp
from .routes.llm_routes import llm_bp
from .routes.ml_routes import ml_bp
from .routes.business_automation_routes import api as business_automation_api

def create_app():
    app = Flask(__name__, template_folder="views/templates")
    app.config.from_object(Config)
    CORS(app, resources={r"/*": {"origins": ["*", "http://localhost:4200"], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)



    # Register your existing blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(llm_bp, url_prefix="/api/llm")
    app.register_blueprint(ml_bp, url_prefix="/api/ml")
    # Initialize Flask-RESTX API with Swagger FIRST
    api = Api(
        app,
        version='1.0',
        title='Business Automation API',
        description='API for automated test case and task generation from user stories',
        doc='/docs/'  # Swagger UI will be at http://localhost:5000/docs/
    )
    
    # Import and register business automation API namespace
    
    api.add_namespace(business_automation_api, path='/business-automation')

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept,Referer,User-Agent')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app