import requests
from flask import current_app
from marshmallow import ValidationError
from models.schemas import login_schema


def login_user(login_data):
    """Authenticate user and return tokens"""
    django_login_url = u'{}/api/token/'.format(current_app.config['DJANGO_API_URL'])

    results = login_schema.load(login_data)
    if results.errors:
        raise ValidationError(results.errors)

    username = results.data.get('username')
    password = results.data.get('password')

    current_app.logger.info(u'Login attempt for user: %s', username)

    response = requests.post(
        django_login_url,
        json={
            "username": username,
            'password': password
        }
    )

    if response.status_code not in (200, 201):
        raise ValidationError({"error": "Invalid credentials", "details": response.text})

    token_data = response.json()
    return {
        "message": "Login successful",
        "access_token": token_data.get("access"),
        "refresh_token": token_data.get("refresh")
    }