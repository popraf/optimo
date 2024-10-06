import os
import logging
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from utils.logging_handler import SQLAlchemyHandler

load_dotenv()

DB_HOST = os.environ.get('DATABASE_HOST')
DB_PORT = os.environ.get('DATABASE_PORT')
DB_USER = os.environ.get('DATABASE_USER')
DB_PASSWORD = os.environ.get('DATABASE_PASSWORD')
DB_NAME = os.environ.get('DATABASE_NAME')


def config_db(app):
    """
    Configure the Flask app with SQLAlchemy and logging.
    """
    # Configure SQLAlchemy with MySQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(
        DB_USER,
        DB_PASSWORD,
        DB_HOST,
        DB_PORT,
        DB_NAME
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db = SQLAlchemy(app)
    return db


def config_handler(db, app):
    # Set up logging with SQLAlchemy
    db_handler = SQLAlchemyHandler(db.session)
    db_handler.setLevel(logging.INFO)

    # Define log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    db_handler.setFormatter(formatter)

    # Remove existing handlers (like the default StreamHandler)
    if app.logger.handlers:
        for handler in app.logger.handlers:
            app.logger.removeHandler(handler)

    # Add the custom database handler
    app.logger.addHandler(db_handler)
    app.logger.setLevel(logging.INFO)
