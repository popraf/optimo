import os
import base64
import hashlib
import functools
import json
from flask import jsonify, request
from Crypto.Cipher import AES


class SimpleAES:
    """I consider HTTPS (SSL/TLS) usage, however this is just for a training purposes
    """
    def __init__(self):
        self.aes_key = os.getenv('AES_KEY')

    def encrypt_data(self, data):
        # Hash the key to ensure it is 32 bytes
        key = hashlib.sha256(self.aes_key.encode()).digest()
        cipher = AES.new(key, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def decrypt_data(self, data):
        # Hash the key to ensure it is 32 bytes
        key = hashlib.sha256(self.aes_key.encode()).digest()
        encrypted_data = base64.b64decode(data)
        nonce = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        return cipher.decrypt(ciphertext).decode('utf-8')


def encrypt_payload(func):
    @functools.wraps(func)
    def wrapper_encrypt(*args, **kwargs):
        try:
            # Load JSON data from request
            data = request.get_json()
            print('JSON DATA: ', data)
            if not data:
                return jsonify({"error": "Missing JSON payload"}), 400

            # Encrypt data using SimpleAES class
            aes_encryption = SimpleAES()
            encrypted_data = aes_encryption.encrypt_data(json.dumps(data))

            # Update kwargs to pass encrypted data
            kwargs['encrypted_data'] = encrypted_data

            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Encryption failed: {}".format(str(e))}), 500

    return wrapper_encrypt
