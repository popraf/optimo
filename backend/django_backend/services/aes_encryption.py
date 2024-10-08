import os
import base64
import hashlib
from Crypto.Cipher import AES
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import AuthenticationFailed


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


class DecryptJWTMiddleware(MiddlewareMixin):
    """
    Middleware to decrypt JWT tokens encrypted with AES.

    This middleware intercepts incoming requests, decrypts the encrypted JWT token 
    in the 'Authorization' header, and updates the request for further processing.
    """
    def process_request(self, request):
        """
        Decorator that decrypts the JWT token in the Authorization header,
          if present, and updates the request.

        Parameters:
        - request: The HTTP request object containing headers.

        Raises:
        - AuthenticationFailed: If the token is invalid or cannot be decrypted.

        Returns:
        - None: Processes the request in-place (decorator).
        """
        aes_encryption = SimpleAES()
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                decrypted_token = aes_encryption.decrypt_data(token)
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {decrypted_token}'
            except Exception as e:
                raise AuthenticationFailed(f'Invalid token: {str(e)}')

        return None
