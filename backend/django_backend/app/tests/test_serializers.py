from django.test import TestCase
from ..serializers import BookSerializer, ReservationSerializer
from .test_data import create_test_user, create_test_book, create_test_reservation


class BookSerializerTest(TestCase):

    def setUp(self):
        self.book_data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn': '1234567890123',
            'count_in_library': 3,
            'library': 'Test Library'
        }
        self.book = create_test_book(**self.book_data)

    def test_book_serialization(self):
        serializer = BookSerializer(self.book)
        data = serializer.data
        self.assertEqual(data['title'], self.book_data['title'])
        self.assertEqual(data['isbn'], self.book_data['isbn'])

    def test_book_deserialization(self):
        serializer = BookSerializer(data=self.book_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['title'], 'Test Book')


class ReservationSerializerTest(TestCase):

    def setUp(self):
        self.user = create_test_user()
        self.book = create_test_book()
        self.reservation = create_test_reservation(self.user, self.book)

    def test_reservation_serialization(self):
        serializer = ReservationSerializer(self.reservation)
        data = serializer.data
        self.assertEqual(data['user'], self.user.username)
        self.assertEqual(data['book'], self.book.id)
