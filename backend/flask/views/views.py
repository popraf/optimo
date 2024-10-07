import requests
import copy
import json
from flask import Blueprint, jsonify, request, current_app
from marshmallow import Schema, fields, ValidationError
from utils.aes_encryption import SimpleAES, encrypt_payload
from tests.mock_data import MOCK_BOOK_DATA
from utils.config import Config


library_manage_blueprint = Blueprint('reservations', __name__)


class ReservationSchema(Schema):
    book_id = fields.Integer(required=True)


class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)


reservation_schema = ReservationSchema()
login_schema = LoginSchema()


@library_manage_blueprint.route('/health', methods=['GET'])
def health_check():
    current_app.logger.info('Health check')
    return jsonify({"status": "healthy"}), 200


@library_manage_blueprint.route('/books/<isbn>/availability', methods=['GET'])
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


@library_manage_blueprint.route('/books/<int:pk>/details', methods=['GET'])
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


@library_manage_blueprint.route('/login', methods=['POST'])
@encrypt_payload
def login(encrypted_data):
    """Login to library endpoint
    """
    # aes_encryption = SimpleAES()
    django_login_url = '{}/api/token/'.format(Config.DJANGO_API_URL)
    try:
        results = login_schema.load(request.json)

        if results.errors:
            # Handle validation errors if there are any
            current_app.logger.error('Validation error: %s', results.errors)
            return jsonify({"error": "Validation error", "messages": results.errors}), 400

        login_data = results.data
        username = login_data.get('username')
        password = login_data.get('password')

        current_app.logger.info('Username: %s', username)
        current_app.logger.info('Password: %s', password)

        response = requests.post(
            django_login_url,
            json={
                "username": username,
                'password': password
                }
            )

        if response.status_code not in (200, 201):
            return jsonify({"error": "Invalid credentials", "details": response.text}), response.status_code

        token_data = response.json()

        return jsonify({
            "message": "Login successful",
            "access_token": token_data.get("access"),
            "refresh_token": token_data.get("refresh")
        }), 200

    except ValidationError as err:
        current_app.logger.error('HTTP error occurred: %s', err)
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    except Exception as e:
        current_app.logger.error('Request exception: %s', str(e))
        return jsonify({"error": "An error occurred: {}".format(str(e))}), 500


@library_manage_blueprint.route('/book_reserved_external/<int:pk>', methods=['POST'])
def book_reserved_external():
    """Endpoint to reserve a book from external library
    """
    aes_encryption = SimpleAES()
    django_verification_url = '{}/api/token/verify/'.format(Config.DJANGO_API_URL)
    try:
        reservation_data = reservation_schema.load(request.json)  # Data validation
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401

        auth_header = aes_encryption.decrypt_data(auth_header)
        jwt_token = auth_header.split(' ')[1]

        # Verify token in Django
        verification_response = requests.post(
            django_verification_url,
            json={"token": jwt_token}
        )

        if verification_response.status_code != 200:
            return jsonify({"error": "Invalid token"}), 403

        # Reserve a book in external library (mock data)
        book = MOCK_BOOK_DATA.get(reservation_data)
        book['count_in_library'] -= 1
        current_app.logger.info('Book %s reserved in external library', reservation_data)
        return jsonify({"message": "Book with id {} reserved successfully"}.format(reservation_data)), 200
    except ValidationError as err:
        current_app.logger.error('HTTP error occurred: %s', err)
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    except Exception as e:
        current_app.logger.error('Request exception: %s', str(e))
        return jsonify({"error": "An error occurred: {}".format(str(e))}), 500


@library_manage_blueprint.route('/reserve/<int:pk>', methods=['POST'])
def reserve():
    """Endpoint to reserve a book via Django endpoint
    """
    aes_encryption = SimpleAES()
    reservation_data = reservation_schema.load(request.json)  # Data validation
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    jwt_token = auth_header.split(' ')[1]
    encrypted_token = aes_encryption.encrypt_data(jwt_token)

    # Django reservation endpoint
    reservation_url = '%s/reservations/reserve/' % Config.DJANGO_API_URL

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % encrypted_token
    }

    try:
        # POST to Django's reservation endpoint
        response = requests.post(
            reservation_url,
            json=reservation_data,
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        # Log the successful reservation
        current_app.logger.info('Reservation confirmed via Django: book_id %s', reservation_data)
        # Return the Django response
        return jsonify({'status': 'Reservation confirmed via Django', 'details': response.json()}), response.status_code
    except requests.exceptions.HTTPError as http_err:
        # Forward the error from the Django app
        current_app.logger.error('HTTP error occurred: %s', http_err)
        return jsonify({'status': 'Failed to reserve via Django', 'error': response.json()}), response.status_code
    except requests.exceptions.RequestException as e:
        current_app.logger.error('Request exception: %s', str(e))
        return jsonify({'status': 'Failed to reserve via Django', 'error': str(e)}), 500
