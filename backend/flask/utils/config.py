import os
import logging
from dotenv import load_dotenv
from .logging_handler import SQLAlchemyHandler

load_dotenv()


class Config(object):
    FLASK_SECRET = os.getenv('FLASK_SECRET')
    DB_HOST = os.environ.get('DATABASE_HOST')
    DB_PORT = os.environ.get('DATABASE_PORT')
    DB_USER = os.environ.get('DATABASE_USER')
    DB_PASSWORD = os.environ.get('DATABASE_PASSWORD')
    DB_NAME = os.environ.get('DATABASE_NAME')
    DJANGO_HOST = os.environ.get('DJANGO_HOST')
    DJANGO_PORT = os.environ.get('DJANGO_PORT')

    DJANGO_API_URL = 'http://{}:{}'.format(DJANGO_HOST, DJANGO_PORT)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(
        DB_USER,
        DB_PASSWORD,
        DB_HOST,
        DB_PORT,
        DB_NAME
    )

    @classmethod
    def init_app(cls, app):
        app.config.from_object(cls)
        # Ensure all environment variables are set
        for key in cls.__dict__:
            if key.isupper() and getattr(cls, key) is None:
                raise ValueError("Environment variable {} is not set".format(key))


class DevConfig(Config):
    FLASK_ENV = 'development'


def log_config_handler(db, app):
    # Set up logging with SQLAlchemy
    session = db.session
    db_handler = SQLAlchemyHandler(session)
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
    logging.basicConfig(level=logging.INFO)
