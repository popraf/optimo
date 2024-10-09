from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from utils.db_init import initialize_database
from utils.config import Config, log_config_handler
from views.views import library_manage_blueprint
from flasgger import Swagger


# Factory function
def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    swagger = Swagger(app)
    app.config.from_object(config_class)
    config_class.init_app(app)

    # Initialize tables
    with app.app_context():  # Ensure an application context is active
        app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db = SQLAlchemy(app)
        initialize_database(app, db, ['flask_logs'])
        log_config_handler(db, app)

    # Register blueprints
    app.register_blueprint(library_manage_blueprint)

    return app
