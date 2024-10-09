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
from flasgger import swag_from

library_manage_blueprint = Blueprint('library_manage', __name__)


@library_manage_blueprint.route('/health', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Health status of the API',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {
                        'type': 'string',
                        'example': 'healthy'
                    }
                }
            }
        }
    }
})
def health_check():
    current_app.logger.info('Health check')
    return jsonify({"status": "healthy"}), 200


@library_manage_blueprint.route('/books/<isbn>/availability', methods=['GET'])
@swag_from({
    'parameters': [
        {
            'name': 'isbn',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ISBN of the book to check availability'
        }
    ],
    'responses': {
        200: {
            'description': 'Book availability information',
            'schema': {
                'type': 'object',
                'properties': {
                    'pk': {
                        'type': 'object',
                        'properties': {
                            'author': {'type': 'string'},
                            'count_in_library': {'type': 'integer'},
                            'isbn': {'type': 'string'},
                            'library': {'type': 'string'},
                            'title': {'type': 'string'}
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Not found books based on ISBN',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
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
@swag_from({
    'parameters': [
        {
            'name': 'pk',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'The primary key (PK) of the book to get details'
        }
    ],
    'responses': {
        200: {
            'description': 'Details of the book',
            'schema': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'author': {'type': 'string'},
                    'isbn': {'type': 'string'},
                    'library': {'type': 'string'},
                    'count_in_library': {'type': 'integer'},
                }
            }
        },
        404: {
            'description': 'Book not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
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
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['username', 'password']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Successful login',
            'schema': {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string'},
                    'refresh_token': {'type': 'string'},
                    'message': {'type': 'string'}
                },
            }
        },
        400: {
            'description': 'Validation error'
        },
        500: {
            'description': 'An error occurred during login'
        }
    }
})
def login():
    """Login to library endpoint"""
    try:
        result = login_user(request.json)
        return jsonify(result), 200
    except HTTPError as http_err:
        response = http_err.response
        return BadRequest(response.text)
    except ValidationError as err:
        current_app.logger.info('Login ValidationError: {}'.format(unicode(err)))
        return error_response(u"Validation error", 400, err.messages)
    except Exception as e:
        current_app.logger.error(u'Login exception: %s', unicode(e))
        return error_response(u"An error occurred during login", 500, e.message)


@library_manage_blueprint.route('/reserve', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'book_id': {'type': 'integer'},
                },
                'required': ['book_id']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Book reserved successfully'
        },
        400: {
            'description': 'Validation error'
        },
        500: {
            'description': 'An unexpected error occurred during reservation'
        }
    }
})
def reserve():
    """Endpoint to reserve a book via Django endpoint"""
    try:
        result, status_code = reserve_book(request.json, request.headers)
        return jsonify(result), status_code
    except HTTPError as http_err:
        response = http_err.response

        if response.status_code == 400:
            return BadRequest(response.text)

        if response.status_code == 401:
            return Unauthorized(response.text)

        current_app.logger.error(u"HTTP error occurred for request %s: %s", request.json, unicode(http_err))
        return error_response(u"An HTTP error occurred", response.status_code, response.text)
    except ValidationError as e:
        return error_response(u"Validation error", 400, e.messages)
    except Unauthorized as e:
        return error_response('Unauthorized', 400, e.message)
    except Exception as e:
        current_app.logger.error(u'Reservation exception in /reserve for request %s: %s', request.json, unicode(e))
        return error_response(u"An unexpected error occurred during reservation:", 500)


@library_manage_blueprint.route('/book_reserved_external', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'book_id': {'type': 'integer'},
                },
                'required': ['book_id']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Book reserved successfully in external library'
        },
        400: {
            'description': 'Validation error'
        },
        500: {
            'description': 'An error occurred during external reservation'
        }
    }
})
def book_reserved_external():
    """Endpoint to reserve a book in external library
    """
    try:
        result = reserve_book_external(request.json, request.headers)
        return jsonify(result), 200
    except ValidationError as e:
        return error_response(u"Validation error", 400, unicode(e))
    except Unauthorized as e:
        return error_response('Unauthorized', 400, e.message)
    except BadRequest as e:
        return error_response('Bad Request', 400, unicode(e))
    except Exception as e:
        current_app.logger.error(u'External reservation exception in /book_reserved_external \
                                 for request %s: %s', request.json, unicode(e))
        return error_response(u"An error occurred during external reservation", 500)
