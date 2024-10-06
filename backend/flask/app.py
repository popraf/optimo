import os
import requests
import json
import copy
from flask import Flask, jsonify, request, abort
from utils.db_init import initialize_database
from utils.config import config_db, config_handler
from tests.mock_data import MOCK_BOOK_DATA


app = Flask(__name__)
db = config_db(app)
config_handler(db, app)


@app.route('/health', methods=['GET'])
def health_check():
    app.logger.info('Health check')
    return jsonify({"status": "healthy"}), 200


@app.route('/books/<isbn>/availability', methods=['GET'])
def check_availability(isbn):
    """
    Endpoint to check book availability in other libraries.
    """
    # External API logic should be applied here.
    # Instead, I simulate it with mock
    books = copy.deepcopy(MOCK_BOOK_DATA)

    books = {key: value for key, value in books.items()
             if str(value['isbn']) == str(isbn) and int(value['count_in_library']) >= 1}

    if not books:
        return jsonify({'error': 'Not found books based on ISBN'}), 404

    return jsonify(books), 200


@app.route('/books/<int:pk>/details', methods=['GET'])
def get_book_details(pk):
    """
    Endpoint to get details about a book.
    """
    book = MOCK_BOOK_DATA.get(pk)
    if book:
        return jsonify({
            'title': book.get('title'),
            'author': book.get('author'),
            'isbn': book.get('isbn'),
            'library': book.get('library'),
            'count_in_library': book.get('count_in_library')
        }), 200
    return jsonify({'error': 'Book not found'}), 404


@app.route('/reserve', methods=['POST'])
def reserve():
    data = request.get_json()
    auth_header = request.headers.get('Authorization')
    if not data or 'book_id' not in data or 'reserved_until' not in data or 'library' not in data:
        abort(400, 'Invalid input data. Must include book_id, reserved_until and library.')
    if not auth_header or not auth_header.startswith('Bearer '):
        abort(401, 'Missing or invalid Authorization header.')

    jwt_token = auth_header.split(' ')[1]
    book_id = data.get('book_id')
    library = data.get('library')
    reserved_until = data.get('reserved_until')

    # Make a request to the Django app's reservation endpoint
    django_api_url = 'http://{}:{}'.format(os.getenv('DJANGO_HOST'), os.getenv('DJANGO_PORT'))  # Django service URL in Docker
    reservation_url = '%s/reservations/reserve/' % django_api_url

    # Prepare the payload for the Django API
    payload = {
        'book_id': book_id,
        'reserved_until': reserved_until,
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
    required_tables = ['flask_logs']
    initialize_database(db, required_tables)
    app.run(host='0.0.0.0', port=os.getenv('FLASK_PORT'))
