import pytest
from app import create_app
from tests.mock_data import MOCK_BOOK_DATA
from utils.config import Config
# import json
# import mock


@pytest.fixture
def client():
    app = create_app(Config)
    with app.test_client() as client:
        yield client


def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


def test_check_availability_found(client):
    # Test with an available ISBN
    isbn = MOCK_BOOK_DATA["1"]["isbn"]
    response = client.get('/books/{}/availability'.format(isbn))
    assert response.status_code == 200
    assert len(response.json) > 0  # There should be at least one book found


def test_check_availability_not_found(client):
    # Test with an unavailable ISBN
    isbn = "999999999"
    response = client.get('/books/{}/availability'.format(isbn))
    assert response.status_code == 404
    assert response.json == {'error': 'Not found books based on ISBN'}


def test_get_book_details_found(client):
    # Test for an available book by pk
    pk = 1
    response = client.get('/books/{}/details'.format(pk))
    assert response.status_code == 200
    book_details = response.json
    assert book_details['title'] == MOCK_BOOK_DATA[str(pk)]['title']
    assert book_details['author'] == MOCK_BOOK_DATA[str(pk)]['author']


def test_get_book_details_not_found(client):
    # Test for an unavailable book by pk
    pk = 999
    response = client.get('/books/{}/details'.format(pk))
    assert response.status_code == 404
    assert response.json == {'error': 'Book not found'}
