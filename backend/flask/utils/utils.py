from flask import jsonify


def error_response(message, status_code, details=None):
    response = {"error": message}
    if details:
        response["details"] = details
    return jsonify(response), status_code
