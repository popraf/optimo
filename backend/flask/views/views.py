import requests
import copy
from flask import jsonify, request, current_app, Blueprint
from marshmallow import ValidationError
from werkzeug.exceptions import BadRequest, Unauthorized
# from utils.aes_encryption import SimpleAES, encrypt_payload
from requests.exceptions import HTTPError
from utils.utils import error_response
from services.services import (
    reserve_book,
    reserve_book_external,
)
from services.auth_services import login_user
from test.mock_data import MOCK_BOOK_DATA

library_manage_blueprint = Blueprint('library_manage', __name__)


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
        return jsonify({'error': 'Not found books based on ISBN'}), 400

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
def login():
    """Login to library endpoint"""
    try:
        result = login_user(request.json)
        return jsonify(result), 200
    except ValidationError as err:
        return error_response(u"Validation error", 400, err.messages)
    except Exception as e:
        current_app.logger.error(u'Login exception: %s', unicode(e))
        return error_response(u"An error occurred during login", 500)


@library_manage_blueprint.route('/reserve/<int:book_id>', methods=['POST'])
def reserve(book_id):
    """Endpoint to reserve a book via Django endpoint"""
    try:
        result, status_code = reserve_book(book_id, request.json, request.headers)
        return jsonify(result), status_code
    except HTTPError as http_err:
        response = http_err.response

        if response.status_code == 400:
            return BadRequest(response.text)

        if response.status_code == 401:
            return Unauthorized(response.text)

        current_app.logger.error(u"HTTP error occurred for book %s: %s", book_id, unicode(http_err))
        return error_response(u"An HTTP error occurred", response.status_code, response.text)
    except ValidationError as err:
        return error_response(u"Validation error", 400, err.messages)
    except Exception as e:
        current_app.logger.error(u'Reservation exception in /reserve for book %s: %s', book_id, unicode(e))
        return error_response(u"An unexpected error occurred during reservation:", 500)


@library_manage_blueprint.route('/book_reserved_external/<int:book_id>', methods=['POST'])
def book_reserved_external(book_id):
    """Endpoint to reserve a book in external library"""
    try:
        result = reserve_book_external(book_id, request.json, request.headers)
        return jsonify(result), 200
    except ValidationError as err:
        return error_response(u"Validation error", 400, err.messages)
    except Exception as e:
        current_app.logger.error(u'External reservation exception in /book_reserved_external \
                                 for book %s: %s', book_id, unicode(e))
        return error_response(u"An error occurred during external reservation", 500)
