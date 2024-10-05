from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Log(db.Model):
    __tablename__ = 'flask_logs'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    level = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return "<Log {}: {}...>".format(self.level, self.message[:20])
