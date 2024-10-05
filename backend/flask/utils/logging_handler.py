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
        from utils.models import Log  # Lazy import / factory pattern / to avoid circular reference
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
