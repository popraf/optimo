import os
import requests
import logging
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class AvailabilityService:
    def __init__(self):
        self.base_flask_api_url = f"http://{os.getenv('FLASK_HOST')}:{os.getenv('FLASK_PORT')}"

    def check_book_availability_flask(self, isbn):
        """
        Calls Flask API to check book availability in other libraries based on ISBN.
        Returns only libraries where book is available.
        """
        request_flask_api_url = f"{self.base_flask_api_url}/books/{isbn}/availability"
        try:
            response = requests.get(request_flask_api_url, timeout=5)
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
            return False

    def reserve_book_external_api(self, pk):
        request_flask_api_url = f"{self.base_flask_api_url}/book_reserved_external/{pk}"
        try:
            response = requests.post(request_flask_api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('message', '').lower().endswith('reserved successfully')
        except RequestException as e:
            logger.error(f"Error calling external API in reserve_book_external_api: {str(e)}")
            return False
        except (KeyError, ValueError) as e:
            logger.error(f"Unexpected response format in reserve_book_external_api: {str(e)}")
            return False
