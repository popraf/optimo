from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from app.serializers import BookSerializer, ReservationSerializer
from app.models import Book, Reservation
from datetime import datetime, timedelta, timezone


class BookSerializerTest(APITestCase):
    def setUp(self):
        self.book_data = {
            'title': 'Test Book',
            'author': 'Author A',
            'isbn': '1234567890123',
            'count_in_library': 5,
            'library': 'Main Library'
        }

    def test_book_serialization(self):
        """
        Test book instance serialization
        """
        book = Book.objects.create(**self.book_data)
        serializer = BookSerializer(book)
        expected_data = {
            'book_id': book.book_id,
            'title': 'Test Book',
            'author': 'Author A',
            'isbn': '1234567890123',
            'count_in_library': 5,
            'library': 'Main Library'
        }
        self.assertEqual(serializer.data, expected_data)

    def test_book_deserialization(self):
        """
        Test book instance deserialization
        """
        serializer = BookSerializer(data=self.book_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        book = serializer.save()
        self.assertIsInstance(book, Book)
        for key, value in self.book_data.items():
            self.assertEqual(getattr(book, key), value)

    def test_book_read_only_fields(self):
        """
        Test Book read only
        """
        self.book_data['book_id'] = 10
        serializer = BookSerializer(data=self.book_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        book = serializer.save()
        self.assertNotEqual(book.book_id, 10)


class ReservationSerializerTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.book = Book.objects.create(
            title='Test Book',
            author='Author A',
            isbn='1234567890123',
            count_in_library=5,
            library='Main Library'
        )
        self.reservation_data = {
            'book': self.book.book_id,
        }

    def test_reservation_serialization(self):
        """
        Test reservation data serializer
        """
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book,
            reserved_until=datetime.now(timezone.utc) + timedelta(days=30),
            reservation_status=True,
            is_external=False
        )
        serializer = ReservationSerializer(reservation)
        expected_data = {
            'reservation_id': reservation.reservation_id,
            'user': self.user.username,
            'book': self.book.book_id,
            'reserved_at': reservation.reserved_at.isoformat().replace('+00:00', 'Z'),
            'reserved_until': reservation.reserved_until.isoformat().replace('+00:00', 'Z'),
            'reservation_status': reservation.reservation_status,
            'is_external': reservation.is_external
        }
        self.assertEqual(serializer.data, expected_data)

    def _get_mock_request(self, user):
        """
        Helper to create mock request with user
        """
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        return Request(request)

    def test_reservation_invalid_book(self):
        """
        Test when the book does not exist
        """
        self.reservation_data['book'] = 999
        serializer = ReservationSerializer(data=self.reservation_data)
        serializer.context['request'] = self._get_mock_request(user=self.user)
        self.assertFalse(serializer.is_valid())
        self.assertIn('book', serializer.errors)
