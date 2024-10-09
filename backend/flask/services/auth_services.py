import requests
from flask import current_app
from marshmallow import ValidationError
from models.schemas import login_schema


def login_user(login_data):
    """Authenticate user and return tokens"""
    django_login_url = u'{}/api/token/'.format(current_app.config['DJANGO_API_URL'])
    try:
        data = login_schema.load(login_data)
        username = data.get('username')
        password = data.get('password')

        current_app.logger.info('Login attempt for user: %s', username)

        response = requests.post(
            django_login_url,
            json={
                "username": username,
                "password": password
            }
        )
        response.raise_for_status()

        token_data = response.json()

        return {
            "message": "Login successful",
            "access_token": token_data.get("access"),
            "refresh_token": token_data.get("refresh")
        }

    except ValidationError as err:
        # Re-raise validation errors to be handled by the calling function
        raise err
    except requests.exceptions.RequestException as e:
        # Handle network-related errors
        current_app.logger.error('Error connecting to Django API: %s', str(e))
        raise Exception("Failed to connect to the authentication service")
    except Exception as e:
        # Handle any other unexpected exceptions
        current_app.logger.error('Unexpected error during login: %s', str(e))
        raise Exception("An unexpected error occurred during login")
