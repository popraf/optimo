import os
import logging
import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from utils.db_init import initialize_database
from utils.config import Config, log_config_handler
from utils.logging_handler import setup_logging
from views.views import library_manage_blueprint


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

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
