import requests
from flask import current_app, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import Unauthorized, BadRequest
from models.schemas import reservation_schema
from test.mock_data import MOCK_BOOK_DATA


def reserve_book(reservation_data, headers):
    validated_data = validate_reservation_data(reservation_data)
    jwt_token = get_jwt_token(headers)
    response = make_reservation_request(validated_data, jwt_token)
    return handle_successful_reservation(response, validated_data)


def validate_reservation_data(data):
    result = reservation_schema.load(data)
    if result.errors:
        current_app.logger.error(u'Validation error: %s', result.errors)
        raise ValidationError(result.errors)
    return result.data


def get_jwt_token(headers):
    auth_header = headers.get('Authorization')
    if not auth_header:
        raise Unauthorized(u"Missing Authorization header")
    return auth_header.split(' ')[1]


def make_reservation_request(reservation_data, jwt_token):
    reservation_url = u'{}/api/reserve/'.format(current_app.config['DJANGO_API_URL'])
    headers = {
        'Content-Type': 'application/json',
        'Authorization': u'Bearer {}'.format(jwt_token)
    }
    response = requests.post(
        reservation_url,
        json=reservation_data,
        headers=headers,
    )
    response.raise_for_status()

    return response


def handle_successful_reservation(response, book_id):
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"detail": response.text}
    return {
        'status': u'Reservation of book {} confirmed via Django'.format(book_id),
        'details': response_data
    }, response.status_code


def reserve_book_external(reservation_data, headers):
    """Reserve a book in external library"""
    django_verification_url = u'{}/api/token/verify/'.format(current_app.config['DJANGO_API_URL'])
    validated_data = validate_reservation_data(reservation_data)
    book_id = validated_data.get('book_id')
    jwt_token = get_jwt_token(headers)

    # Verify token in Django
    verification_response = requests.post(
        django_verification_url,
        json={"token": jwt_token}
    )

    if verification_response.status_code != 200:
        raise Unauthorized(u"Invalid token")

    # Reserve a book in external library (mock data)
    book = MOCK_BOOK_DATA.get(book_id)

    if not book or book['count_in_library'] < 1:
        raise BadRequest(u"Book {} not available in external library".format(book_id))

    book['count_in_library'] -= 1
    return {"message": u"Book with id {} reserved successfully".format(book_id)}
