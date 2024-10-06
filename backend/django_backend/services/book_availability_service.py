import requests
from requests.exceptions import RequestException


class AvailabilityService:
    def __init__(self):
        self.base_flask_api_url = "https://api.externallibrary.com/books/"

    def check_book_availability_flask(self, isbn):
        """
        Calls Flask API to check book availability in other libraries based on ISBN.
        """
        request_flask_api_url = f"{self.base_flask_api_url}/{isbn}/availability"
        try:
            response = requests.get(request_flask_api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('available', False)
        except RequestException as e:
            # Handle errors gracefully, possibly log for debugging purposes
            print(f"Error calling external API: {e}")
            return False

    def get_book_details(self, pk):
        request_flask_api_url = f"{self.base_flask_api_url}/{pk}/details"
        try:
            response = requests.get(request_flask_api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('available', False)
        except RequestException as e:
            # Handle errors gracefully, possibly log for debugging purposes
            print(f"Error calling external API: {e}")
            return False

    def reserve_book_external_api(self, pk):
        request_flask_api_url = f"{self.base_flask_api_url}/{pk}/reserve"
        try:
            response = requests.get(request_flask_api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('available', False)
        except RequestException as e:
            # Handle errors gracefully, possibly log for debugging purposes
            print(f"Error calling external API: {e}")
            return False
