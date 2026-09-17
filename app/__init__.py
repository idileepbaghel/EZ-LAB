from flask import Flask
from config import Config

def create_app(config_class=Config):
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    
    # Load configuration (this automatically sets up app.secret_key for sessions)
    app.config.from_object(config_class)


    # Import and register your raw SQL blueprints
    from .main.auth import auth_bp
    from .main.master import master_bp
    from .main.dashboard import dashboard_bp


    app.register_blueprint(auth_bp)
    app.register_blueprint(master_bp, url_prefix='/master')
    app.register_blueprint(dashboard_bp)


    return app