from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from .test_data import create_test_user, create_test_book, create_test_reservation


class BookViewSetTest(APITestCase):

    def setUp(self):
        self.book = create_test_book()

    def test_list_books(self):
        response = self.client.get('/books/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_by_isbn(self):
        response = self.client.get('/books/search_by_isbn/?isbn=1234567890123')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['title'], 'Test Book')


class UserReservationListViewTest(APITestCase):

    def setUp(self):
        self.user = create_test_user()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.book = create_test_book()
        self.reservation = create_test_reservation(self.user, self.book)

    def test_user_reservations_list(self):
        response = self.client.get('/reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['book'], self.book.id)


class ReserveBookViewTest(APITestCase):

    def setUp(self):
        self.user = create_test_user()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.book = create_test_book(count_in_library=1)

    def test_reserve_book(self):
        response = self.client.post('/reserve/', {'book': self.book.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.count_in_library, 0)

    def test_reserve_book_not_available(self):
        # Reserve the book first to make it unavailable
        create_test_reservation(self.user, self.book)
        response = self.client.post('/reserve/', {'book': self.book.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
