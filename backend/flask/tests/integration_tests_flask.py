import pytest
import json
import mock
from flask import Flask
from app import app as flask_app
from tests.mock_data import MOCK_BOOK_DATA


@mock.patch('requests.post')
def test_reserve_success(mock_post, client):
    # Mock data for the request payload
    book_id = 1
    library = "Library 1"
    reserved_until = "2023-12-31"
    payload = {
        'book_id': book_id,
        'library': library,
        'reserved_until': reserved_until
    }
    
    # Mock successful response from Django API
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'reservation': 'success'}
    mock_post.return_value = mock_response

    response = client.post('/reserve', data=json.dumps(payload), content_type='application/json', headers={
        'Authorization': 'Bearer somevalidtoken'
    })

    assert response.status_code == 200
    response_data = response.json
    assert response_data['status'] == 'Reservation confirmed via Django'
    assert response_data['details'] == {'reservation': 'success'}


@mock.patch('requests.post')
def test_reserve_missing_authorization(mock_post, client):
    # Test reserve with missing Authorization header
    book_id = 1
    library = "Library 1"
    reserved_until = "2023-12-31"
    payload = {
        'book_id': book_id,
        'library': library,
        'reserved_until': reserved_until
    }

    response = client.post('/reserve', data=json.dumps(payload), content_type='application/json')

    assert response.status_code == 401
    assert response.json == {'message': 'Missing or invalid Authorization header.'}


@mock.patch('requests.post')
def test_reserve_invalid_data(mock_post, client):
    # Test reserve with invalid payload
    payload = {
        'library': "Library 1"
        # Missing book_id and reserved_until
    }

    response = client.post('/reserve', data=json.dumps(payload), content_type='application/json', headers={
        'Authorization': 'Bearer somevalidtoken'
    })

    assert response.status_code == 400
    assert 'Invalid input data.' in response.json['message']


@mock.patch('requests.post')
def test_reserve_django_api_failure(mock_post, client):
    # Test the reserve endpoint with Django API failure
    book_id = 1
    library = "Library 1"
    reserved_until = "2023-12-31"
    payload = {
        'book_id': book_id,
        'library': library,
        'reserved_until': reserved_until
    }

    # Mock failed response from Django API
    mock_response = mock.Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {'error': 'Internal server error'}
    mock_post.return_value = mock_response

    response = client.post('/reserve', data=json.dumps(payload), content_type='application/json', headers={
        'Authorization': 'Bearer somevalidtoken'
    })

    assert response.status_code == 500
    response_data = response.json
    assert response_data['status'] == 'Failed to reserve via Django'
    assert 'Internal server error' in response_data['error']
