import logging
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SQLAlchemyHandler(logging.Handler):
    """
    Custom SQLAlchemy logging handler
    """
    def __init__(self, db_session):
        logging.Handler.__init__(self)
        self.db_session = db_session

    def emit(self, record):
        from models import Log  # Lazy import / factory pattern / to avoid circular reference
        try:
            log_entry = Log(
                timestamp=datetime.fromtimestamp(record.created),
                level=record.levelname,
                message=self.format(record)
            )
            self.db_session.add(log_entry)
            self.db_session.commit()
        except Exception:
            self.handleError(record)


def setup_logging(app, db):
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
