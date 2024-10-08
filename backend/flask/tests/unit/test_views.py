import pytest
import json
from flask import Flask
from mock import patch, MagicMock
from flask.testing import FlaskClient
from views.views import library_manage_blueprint
from utils.config import Config
from tests.mock_data import MOCK_BOOK_DATA
from requests.exceptions import HTTPError


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(library_manage_blueprint)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


def test_check_availability_books_found(client, monkeypatch):
    test_isbn = '123123'
    test_book_data = MOCK_BOOK_DATA.copy()
    monkeypatch.setattr('tests.mock_data.MOCK_BOOK_DATA', test_book_data)
    response = client.get('/books/{}/availability'.format(test_isbn))
    assert response.status_code == 200
    expected_books = {str(k): v for k, v in test_book_data.items()
                      if str(v['isbn']) == test_isbn and v['count_in_library'] >= 1}
    assert response.json == expected_books


def test_check_availability_no_books_found(client, monkeypatch):
    test_isbn = '999999'
    test_book_data = MOCK_BOOK_DATA.copy()
    monkeypatch.setattr('tests.mock_data.MOCK_BOOK_DATA', test_book_data)
    response = client.get('/books/{}/availability'.format(test_isbn))
    assert response.status_code == 400
    assert response.json == {'error': 'Not found books based on ISBN'}


def test_get_book_details_found(client, monkeypatch):
    test_pk = 1
    test_book_data = MOCK_BOOK_DATA.copy()
    monkeypatch.setattr('tests.mock_data.MOCK_BOOK_DATA', test_book_data)
    response = client.get('/books/{}/details'.format(test_pk))
    assert response.status_code == 200
    expected_response = {
        'title': test_book_data[test_pk]['title'],
        'author': test_book_data[test_pk]['author'],
        'isbn': test_book_data[test_pk]['isbn'],
        'library': test_book_data[test_pk]['library'],
        'count_in_library': test_book_data[test_pk]['count_in_library']
    }
    assert response.json == expected_response


def test_get_book_details_not_found(client, monkeypatch):
    test_pk = 99  # Non-existent book ID
    test_book_data = MOCK_BOOK_DATA.copy()
    monkeypatch.setattr('tests.mock_data.MOCK_BOOK_DATA', test_book_data)
    response = client.get('/books/{}/details'.format(test_pk))
    assert response.status_code == 404
    assert response.json == {'error': 'Book not found'}


def test_book_reserved_external_success(client, monkeypatch):
    test_pk = 1  # Book with count_in_library >=1
    test_book_data = MOCK_BOOK_DATA.copy()
    monkeypatch.setattr('tests.mock_data.MOCK_BOOK_DATA', test_book_data)

    with patch('views.views.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        headers = {'Authorization': 'Bearer valid_token'}
        data = {'book_id': test_pk}
        response = client.post('/book_reserved_external/{}'.format(test_pk),
                               json=data,
                               headers=headers
                               )
        assert response.status_code == 200
        assert response.json == {'message': 'Book with id {} reserved successfully'.format(test_pk)}
        assert test_book_data[test_pk]['count_in_library'] == MOCK_BOOK_DATA[test_pk]['count_in_library'] - 1
        mock_post.assert_called_with(
            '{}/api/token/verify/'.format(Config.DJANGO_API_URL),
            json={'token': 'valid_token'}
        )


def test_book_reserved_external_book_not_available(client, monkeypatch):
    test_pk = 6  # Book with count_in_library == 0
    test_book_data = MOCK_BOOK_DATA.copy()
    monkeypatch.setattr('tests.mock_data.MOCK_BOOK_DATA', test_book_data)

    with patch('views.views.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        headers = {'Authorization': 'Bearer valid_token'}
        data = {'book_id': test_pk}
        response = client.post('/book_reserved_external/{}'.format(test_pk),
                               json=data,
                               headers=headers
                               )
        assert response.status_code == 400
        assert response.json == {'error': 'Book {} not available in external library'.format(test_pk)}
        assert test_book_data[test_pk]['count_in_library'] == 0


def test_book_reserved_external_invalid_token(client, monkeypatch):
    test_pk = 1
    test_book_data = MOCK_BOOK_DATA.copy()
    monkeypatch.setattr('tests.mock_data.MOCK_BOOK_DATA', test_book_data)

    with patch('views.views.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response
        headers = {'Authorization': 'Bearer invalid_token'}
        data = {'book_id': test_pk}
        response = client.post('/book_reserved_external/{}'.format(test_pk),
                               json=data,
                               headers=headers
                               )
        assert response.status_code == 403
        assert response.json == {'error': 'Invalid token'}
        assert test_book_data[test_pk]['count_in_library'] == MOCK_BOOK_DATA[test_pk]['count_in_library']


def test_book_reserved_external_missing_auth_header(client, monkeypatch):
    test_pk = 1
    test_book_data = MOCK_BOOK_DATA.copy()
    monkeypatch.setattr('tests.mock_data.MOCK_BOOK_DATA', test_book_data)
    data = {'book_id': test_pk}
    response = client.post('/book_reserved_external/{}'.format(test_pk), json=data)
    assert response.status_code == 401
    assert response.json == {'error': 'Missing Authorization header'}


def test_login_success(client):
    login_data = {
        'username': 'testuser',
        'password': 'testpassword'
    }

    with patch('views.views.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access': 'access_token',
            'refresh': 'refresh_token'
        }
        mock_post.return_value = mock_response
        response = client.post('/login', json=login_data)
        assert response.status_code == 200
        assert response.json == {
            'message': 'Login successful',
            'access_token': 'access_token',
            'refresh_token': 'refresh_token'
        }
        mock_post.assert_called_with(
            '{}/api/token/'.format(Config.DJANGO_API_URL),
            json=login_data
        )


def test_login_invalid_credentials(client):
    login_data = {
        'username': 'testuser',
        'password': 'wrongpassword'
    }
    with patch('views.views.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Invalid credentials'
        mock_post.return_value = mock_response
        response = client.post('/login', json=login_data)
        assert response.status_code == 401
        assert response.json == {
            'error': 'Invalid credentials',
            'details': 'Invalid credentials'
        }
        mock_post.assert_called_with(
            '{}/api/token/'.format(Config.DJANGO_API_URL),
            json=login_data
        )


def test_login_validation_error(client):
    login_data = {
        'username': 'testuser',
    }
    response = client.post('/login', json=login_data)
    assert response.status_code == 400
    assert response.json['error'] == 'Validation error'
    assert 'messages' in response.json


def test_reserve_success(client):
    test_pk = 1
    reservation_data = {'book_id': test_pk}

    with patch('views.views.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'status': 'Reservation created'}
        mock_post.return_value = mock_response
        headers = {'Authorization': 'Bearer valid_token'}
        response = client.post('/reserve/{}'.format(test_pk),
                               json=reservation_data,
                               headers=headers
                               )
        assert response.status_code == 201
        assert response.json == {
            'status': 'Reservation confirmed via Django',
            'details': {'status': 'Reservation created'}
            }
        mock_post.assert_called_with(
            '{}/api/reserve/'.format(Config.DJANGO_API_URL),
            json=reservation_data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer valid_token'
            },
            timeout=5
        )


def test_reserve_django_api_unauthorized(client):
    test_pk = 1
    reservation_data = {'book_id': test_pk}

    with patch('views.views.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "Reservation failed"
        }
        mock_response.raise_for_status.side_effect = HTTPError(
            "401 Client Error: Unauthorized",
            response=mock_response
        )
        mock_post.return_value = mock_response
        headers = {'Authorization': 'Bearer valid_token'}
        response = client.post('/reserve/{}'.format(test_pk),
                               json=reservation_data,
                               headers=headers
                               )
        assert response.status_code == 401
        assert response.json['status'] == "Failed to reserve via Django"
        assert response.json['error'] == {
            "error": "Reservation failed"
        }


def test_reserve_missing_auth_header(client):
    test_pk = 1
    reservation_data = {'book_id': test_pk}
    response = client.post('/reserve/{}'.format(test_pk), json=reservation_data)
    assert response.status_code == 401
    assert response.json == {'error': 'Missing Authorization header'}


def test_reserve_validation_error(client):
    test_pk = 1
    reservation_data = {}
    headers = {'Authorization': 'Bearer valid_token'}
    response = client.post('/reserve/{}'.format(test_pk), json=reservation_data, headers=headers)
    assert response.status_code == 400
    assert response.json['error'] == 'Validation error'
    assert 'messages' in response.json
