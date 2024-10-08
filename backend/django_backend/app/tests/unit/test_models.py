from django.test import TestCase
from django.contrib.auth.models import User
from app.models import Book, Reservation


class BookModelTest(TestCase):
    """Test model add a book
    """
    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book",
            author="Author A",
            isbn="1234567890123",
            count_in_library=5
        )

    def test_book_creation(self):
        self.assertEqual(self.book.title, "Test Book")
        self.assertEqual(self.book.count_in_library, 5)


class ReservationModelTest(TestCase):
    """Test model create reservation
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.book = Book.objects.create(
            title="Test Book",
            author="Author A",
            isbn="1234567890123",
            count_in_library=5
        )
        self.reservation = Reservation.objects.create(
            user=self.user,
            book=self.book,
            reserved_until="2023-12-31T00:00:00Z"
        )

    def test_reservation_creation(self):
        self.assertEqual(self.reservation.user.username, 'testuser')
        self.assertEqual(self.reservation.book.title, 'Test Book')
