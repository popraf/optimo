from django.test import TestCase
from .test_data import create_test_user, create_test_book, create_test_reservation


class BookModelTest(TestCase):

    def setUp(self):
        self.book = create_test_book()

    def test_book_creation(self):
        self.assertEqual(self.book.title, 'Test Book')
        self.assertEqual(self.book.count_in_library, 3)
        self.assertEqual(str(self.book), 'Test Book')

    def test_unique_isbn(self):
        with self.assertRaises(Exception):
            create_test_book(isbn='1234567890123')


class ReservationModelTest(TestCase):

    def setUp(self):
        self.user = create_test_user()
        self.book = create_test_book()
        self.reservation = create_test_reservation(self.user, self.book)

    def test_reservation_creation(self):
        self.assertEqual(self.reservation.user.username, 'testuser')
        self.assertEqual(self.reservation.book.title, 'Test Book')
        self.assertTrue(self.reservation.reservation_status)

    def test_unique_reservation(self):
        with self.assertRaises(Exception):
            create_test_reservation(self.user, self.book)
