import os
import requests
import logging
import asyncio
import aiohttp
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class AvailabilityService:
    def __init__(self):
        self.base_flask_api_url = f"http://{os.getenv('FLASK_HOST')}:{os.getenv('FLASK_PORT')}"
        self.session = self._get_retry_session()

    def _get_retry_session(self,
                           retries=3,
                           backoff_factor=0.3,
                           status_forcelist=(500, 502, 503, 504)
                           ):
        """
        Parameters:
        - retries (int): The number of retry attempts for each request. Default is 3.
        - backoff_factor (float): A factor used to calculate the delay between retries.
          A backoff_factor of 0.3 means that the delay will increase by 0.3, 0.6, 1.2, etc.
          for consecutive failures.
        - status_forcelist (tuple of int): HTTP status codes that should trigger a retry.
          By default, retry on server error status codes 500, 502, 503, 504.

        Returns:
        - session (requests.Session): A session object with retry configuration.
        """
        session = requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def check_book_availability_flask(self, isbn):
        """
        Calls Flask API to check book availability in other libraries based on ISBN.
        Returns only libraries where book is available.

        Parameters:
        - isbn (str): The ISBN of the book to check availability for.

        Returns:
        - dict: A dictionary containing libraries where the book
            is available and the count in each library.
          Example: { 'library_name': {'library': 'Library A', 'count_in_library': 5} }
          Returns empty dict in case of no books available
        """
        request_flask_api_url = f"{self.base_flask_api_url}/books/{isbn}/availability"
        try:
            response = self.session.get(request_flask_api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            data = {
                key:
                    {
                        'library': value['library'],
                        'count_in_library': value['count_in_library']
                     } for key, value in data.items()
                     }
            return data
        except RequestException as e:
            logger.error(f"Error calling external API in check_book_availability_flask: {str(e)}")
            raise

    async def async_check_book_availability_flask(self, isbn):
        """
        Asynchronously calls Flask API to check book availability in other libraries based on ISBN.
        Returns only libraries where book is available.

        Parameters:
        - isbn (str): The ISBN of the book to check availability for.

        Returns:
        - dict: A dictionary containing libraries where the book
          is available and the count in each library.
        """
        request_flask_api_url = f"{self.base_flask_api_url}/books/{isbn}/availability"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(request_flask_api_url, timeout=5) as response:
                    response.raise_for_status()
                    data = await response.json()
                    data = {
                        key: {
                            'library': value['library'],
                            'count_in_library': value['count_in_library']
                        } for key, value in data.items()
                    }
                    return data
            except aiohttp.ClientError as e:
                logger.error(f"Error calling external API in async_check_book_availability_flask: {str(e)}")
                raise

    def reserve_book_external_api(self, pk, token):
        """
        Calls Flask API to reserve a book in external library using a unique identifier.

        Parameters:
        - pk (int): The primary key or unique identifier of the book to reserve.

        Returns:
        - bool: True if the reservation is successful, False otherwise.
        """
        request_flask_api_url = f"{self.base_flask_api_url}/book_reserved_external"
        try:
            if not token:
                # Handle missing Authorization header
                raise ValueError("Missing Authorization header")

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            session = self.session
            session.headers.update(headers)
            response = session.post(request_flask_api_url, json={'book_id': pk}, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('message', '').lower().endswith('reserved successfully')
        except RequestException as e:
            logger.error(f"Error calling external API in reserve_book_external_api: {str(e)}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Unexpected response format in reserve_book_external_api: {str(e)}")
            raise
