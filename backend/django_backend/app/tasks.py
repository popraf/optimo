from celery import shared_task
from .models import Book
import requests

@shared_task
def update_book_status():
    books = Book.objects.all()
    for book in books:
        flask_api_url = f"http://flask:8005/status/{book.external_id}"
        try:
            response = requests.get(flask_api_url)
            response.raise_for_status()
            data = response.json()
            book.status = data.get('status', 'unknown')
            book.save()
        except requests.RequestException:
            pass
