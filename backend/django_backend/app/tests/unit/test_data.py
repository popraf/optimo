from django.contrib.auth.models import User
from datetime import datetime, timedelta
from app.models import Book, Reservation


def create_test_user(username='testuser', password='testpassword'):
    return User.objects.create_user(username=username, password=password)


def create_test_book(
        title='Test Book',
        author='Test Author',
        isbn='1234567890123',
        count_in_library=3,
        library='Test Library'):
    return Book.objects.create(
        title=title,
        author=author,
        isbn=isbn,
        count_in_library=count_in_library,
        library=library
    )


def create_test_reservation(user, book, reserved_until=None):
    if reserved_until is None:
        reserved_until = datetime.now() + timedelta(days=30)
    return Reservation.objects.create(
        user=user,
        book=book,
        reserved_until=reserved_until
    )
