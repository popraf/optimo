import pytest
import json
from flask import Flask
from mock import patch, MagicMock
from views.views import library_manage_blueprint
from utils.config import DevConfig
from tests.mock_data import MOCK_BOOK_DATA
from requests.exceptions import HTTPError
from werkzeug.exceptions import Unauthorized, BadRequest
from marshmallow import ValidationError


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(DevConfig)
    app.register_blueprint(library_manage_blueprint)
    return app


@pytest.fixture
def client(app):
    yield app.test_client()


def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


def test_check_availability_success(client):
    isbn = MOCK_BOOK_DATA[1]['isbn']
    response = client.get('/books/{}/availability'.format(isbn))
    assert response.status_code == 200
    assert len(response.json) > 0


def test_check_availability_failure(client):
    isbn = 'nonexistent_isbn'
    response = client.get('/books/{}/availability'.format(isbn))
    assert response.status_code == 400
    assert response.json == {'error': 'Not found books based on ISBN'}


def test_get_book_details_success(client):
    book_id = 1
    response = client.get('/books/{}/details'.format(book_id))
    assert response.status_code == 200
    assert response.json['title'] == MOCK_BOOK_DATA[book_id]['title']


def test_get_book_details_failure(client):
    book_id = 9999
    response = client.get('/books/{}/details'.format(book_id))
    assert response.status_code == 404
    assert response.json == {'error': 'Book not found'}


@patch('views.views.login_user')
def test_login_success(mock_login_user, client):
    mock_login_user.return_value = {
        "message": "Login successful",
        "access_token": "fake_access_token"
        }
    login_data = {
        "username": "test_user",
        "password": "test_password"
    }
    response = client.post('/login', data=json.dumps(login_data), content_type='application/json')
    assert response.status_code == 200
    assert response.json['message'] == 'Login successful'


@patch('views.views.login_user', side_effect=ValidationError('Invalid input'))
def test_login_validation_error(mock_login_user, client):
    login_data = {
        "username": "",
        "password": ""
    }
    response = client.post('/login', data=json.dumps(login_data), content_type='application/json')
    assert response.status_code == 400
    assert 'Validation error' in response.json['error']


@patch('views.views.reserve_book')
def test_reserve_success(mock_reserve_book, client):
    mock_reserve_book.return_value = ({"message": "Reservation successful"}, 200)
    book_id = 1
    reservation_data = {
        "user_id": 123
    }
    response = client.post('/reserve/{}'.format(book_id),
                           data=json.dumps(reservation_data),
                           content_type='application/json'
                           )
    assert response.status_code == 200
    assert response.json['message'] == 'Reservation successful'


@patch('views.views.reserve_book', side_effect=HTTPError(response=MagicMock(status_code=401,
                                                                            text='Unauthorized')))
def test_reserve_unauthorized(mock_reserve_book, client):
    book_id = 1
    reservation_data = {
        "user_id": 123
    }
    response = client.post('/reserve/{}'.format(book_id),
                           data=json.dumps(reservation_data),
                           content_type='application/json')
    assert response.status_code == 401
    assert 'Unauthorized' in response.data


@patch('views.views.reserve_book_external')
def test_book_reserved_external_success(mock_reserve_book_external, client):
    mock_reserve_book_external.return_value = {"message": "External reservation successful"}
    book_id = 2
    reservation_data = {
        "user_id": 456
    }
    response = client.post('/book_reserved_external/{}'.format(book_id),
                           data=json.dumps(reservation_data),
                           content_type='application/json')
    assert response.status_code == 200
    assert response.json['message'] == 'External reservation successful'


def test_book_reserved_external_validation_error(client):
    book_id = 3
    reservation_data = {}
    with patch('views.views.reserve_book_external', side_effect=ValidationError('Invalid data')):
        response = client.post('/book_reserved_external/{}'.format(book_id),
                               data=json.dumps(reservation_data),
                               content_type='application/json')
        assert response.status_code == 400
        assert 'Validation error' in response.json['error']
