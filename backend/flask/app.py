from flask import Flask, jsonify, request, abort
import logging
import requests  # Add this import if not already present
import json

app = Flask(__name__)
logging.basicConfig(filename='flask_app.log', level=logging.INFO)

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


@app.route('/status/<int:book_id>', methods=['GET'])
def status(book_id):
    book_info = external_book_status.get(book_id)
    if book_info is None:
        # Book ID not found in the external service
        app.logger.info('Status request for unknown book_id %s' % book_id)
        return jsonify({'book_id': book_id, 'availability': {}}), 404
    else:
        availability = book_info.get('data', {})
        app.logger.info('Status request for book_id %s: Availability=%s' % (book_id, availability))
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
        app.logger.info('Reservation confirmed via Django: book_id %s, library %s' % (book_id, library))
        # Return the Django response
        return jsonify({'status': 'Reservation confirmed via Django', 'details': response.json()}), response.status_code
    except requests.exceptions.HTTPError as http_err:
        # Forward the error from the Django app
        app.logger.error('HTTP error occurred: %s' % http_err)
        return jsonify({'status': 'Failed to reserve via Django', 'error': response.json()}), response.status_code
    except requests.exceptions.RequestException as e:
        app.logger.error('Request exception: %s' % e)
        return jsonify({'status': 'Failed to reserve via Django', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8005)
