import os
import logging
import requests
import json
import sys
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import inspect
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Fetch environment variables
DB_HOST = os.environ.get('DATABASE_HOST')
DB_PORT = os.environ.get('DATABASE_PORT')
DB_USER = os.environ.get('DATABASE_USER')
DB_PASSWORD = os.environ.get('DATABASE_PASSWORD')
DB_NAME = 'optimo_mysql_db'

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


# Define the Log model
class Log(db.Model):
    __tablename__ = 'flask_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    level = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return "<Log {}: {}...>".format(self.level, self.message[:20])


# Custom SQLAlchemy logging handler
class SQLAlchemyHandler(logging.Handler):
    def __init__(self, db_session):
        logging.Handler.__init__(self)
        self.db_session = db_session

    def emit(self, record):
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

# Configure logging
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

# Mock sample data for book status in different libraries
external_book_status = {
    1: {
        'data': {
            'library 2': True,
            'library 3': False,
            'library 4': True
        }
    },
    2: {
        'data': {
            'library 2': False,
            'library 3': True,
            'library 4': True
        }
    },
    3: {
        'data': {
            'library 2': True,
        }
    },
    4: {
        'data': {
            'library 4': False
        }
    },
    5: {
        'data': {
            'library 2': False,
            'library 3': False,
            'library 4': False
        }
    },
}


def initialize_database(required_tables):
    """
    Check if required tables exist in the database.
    If a table does not exist, create it.
    """
    engine = db.engine
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    missing_tables = [table for table in required_tables if table not in existing_tables]

    if missing_tables:
        print("Missing tables detected: {}".format(", ".join(missing_tables)))
        try:
            db.create_all()  # This will create all tables defined by SQLAlchemy models
            print("Missing tables have been created.")
        except Exception as e:
            print("Error creating tables: {}".format(e))
            sys.exit(1)
    else:
        print("All required tables are present.")


@app.route('/health', methods=['GET'])
def health_check():
    app.logger.info('Health check')
    return jsonify({"status": "healthy"}), 200


@app.route('/status/<int:book_id>', methods=['GET'])
def status(book_id):
    book_info = external_book_status.get(book_id)
    if book_info is None:
        # Book ID not found in the external service
        app.logger.info('Status request for unknown book_id %s', book_id)
        return jsonify({'book_id': book_id, 'availability': {}}), 404
    else:
        availability = book_info.get('data', {})
        app.logger.info('Status request for book_id %s: Availability=%s', book_id, availability)
        return jsonify({'book_id': book_id, 'availability': availability}), 200


@app.route('/reserve', methods=['POST'])
def reserve():
    data = request.get_json()
    auth_header = request.headers.get('Authorization')
    if not data or 'book_id' not in data or 'library' not in data:
        abort(400, 'Invalid input data. Must include book_id and library.')
    if not auth_header or not auth_header.startswith('Bearer '):
        abort(401, 'Missing or invalid Authorization header.')
    
    jwt_token = auth_header.split(' ')[1]
    book_id = data.get('book_id')
    library = data.get('library')

    # Make a request to the Django app's reservation endpoint
    django_api_url = 'http://optimo-django:8000'  # Django service URL in Docker
    reservation_url = '%s/reservations/reserve/' % django_api_url

    # Prepare the payload for the Django API
    payload = {
        'book_id': book_id,
        'reserved_until': '2024-12-31T23:59:59',  # Adjust as needed
        'library': library
    }

    # Prepare headers, including the JWT token
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % jwt_token
    }

    try:
        # Make the POST request to Django's reservation endpoint
        response = requests.post(
            reservation_url,
            data=json.dumps(payload),
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        # Log the successful reservation
        app.logger.info('Reservation confirmed via Django: book_id %s, library %s', book_id, library)
        # Return the Django response
        return jsonify({'status': 'Reservation confirmed via Django', 'details': response.json()}), response.status_code
    except requests.exceptions.HTTPError as http_err:
        # Forward the error from the Django app
        app.logger.error('HTTP error occurred: %s', http_err)
        return jsonify({'status': 'Failed to reserve via Django', 'error': response.json()}), response.status_code
    except requests.exceptions.RequestException as e:
        app.logger.error('Request exception: %s', e)
        return jsonify({'status': 'Failed to reserve via Django', 'error': str(e)}), 500


if __name__ == '__main__':
    required_tables = ['logs']
    initialize_database(required_tables)
    app.run(host='0.0.0.0', port=8005)
