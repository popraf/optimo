from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from app.models import Book, Reservation
from app.serializers import BookSerializer, ReservationSerializer
from datetime import datetime, timedelta
from unittest.mock import patch


class BookAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.admin_user = User.objects.create_superuser(
            username='adminuser', password='password', email='admin@example.com'
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Author A",
            isbn="1234567890123",
            count_in_library=5,
            library='Main Library'
        )
        self.client = APIClient()

    def test_book_list_status(self):
        """
        Test view book add request status only
        """
        url = reverse('book-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_book_data(self):
        """
        Test view book data added
        """
        url = reverse('book-list')
        response = self.client.get(url)
        data = response.json()
        expected_data = {
            'book_id': self.book.book_id,
            'title': 'Test Book',
            'author': 'Author A',
            'isbn': '1234567890123',
            'count_in_library': 5,
            'library': 'Main Library'
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data[0], expected_data)

    def test_add_book_by_normal_user(self):
        """
        Test view that a normal user cannot add a book
        """
        # Authenticate as normal user
        self.client.force_authenticate(user=self.user)
        url = reverse('book_list_create')  # URL for BookListCreateView
        data = {
            'title': 'Normal User Book',
            'author': 'Author X',
            'isbn': '0000000000000',
            'count_in_library': 1,
            'library': 'Main Library'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Book.objects.filter(title='Normal User Book').exists())
        self.client.force_authenticate(user=None)

    def test_add_book_by_admin_user(self):
        """
        Test view that an admin user can add a book successfully
        """
        # Authenticate as admin user
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('book_list_create')  # URL for BookListCreateView
        data = {
            'title': 'Admin User Book',
            'author': 'Author Y',
            'isbn': '1111111111111',
            'count_in_library': 5,
            'library': 'Main Library'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Book.objects.filter(title='Admin User Book').exists())
        self.client.force_authenticate(user=None)

    def test_search_book_by_isbn(self):
        """
        Test view searching for a book by ISBN
        """
        book = Book.objects.create(
            title='Searchable Book',
            author='Author Z',
            isbn='2222222222222',
            count_in_library=3,
            library='Main Library'
        )
        url = reverse('book-search-by-isbn')  # URL for the search_by_isbn action
        url += f'?isbn={book.isbn}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_data = BookSerializer([book], many=True).data
        self.assertEqual(data, expected_data)


class ReturnBookViewTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        self.book = Book.objects.create(
            title='Test Book',
            author='Author A',
            isbn='1234567890123',
            count_in_library=0,
            library='Main Library'
        )
        self.reservation = Reservation.objects.create(
            user=self.user1,
            book=self.book,
            reserved_until=datetime.now() + timedelta(days=30),
            reservation_status=True,
            reservation_library=self.book.library,
            is_external=False
        )
        self.client = APIClient()

    def test_return_book_success(self):
        """
        Test that user can successfully return a reserved book
        """
        self.client.force_authenticate(user=self.user1)
        url = reverse('return_book', args=[self.book.book_id])
        data = {'reservation_id': self.reservation.reservation_id}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Book returned successfully')
        self.reservation.refresh_from_db()
        self.assertFalse(self.reservation.reservation_status)
        self.book.refresh_from_db()
        self.assertEqual(self.book.count_in_library, 1)

    def test_return_book_not_authenticated(self):
        """
        Test that unauthenticated user cannot return a book
        """
        url = reverse('return_book', args=[self.book.book_id])
        data = {'reservation_id': self.reservation.reservation_id}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_return_nonexistent_book(self):
        """
        Test thats returning a non-existent book returns status
        """
        self.client.force_authenticate(user=self.user1)
        non_existent_book_id = 999
        url = reverse('return_book', args=[non_existent_book_id])
        data = {'reservation_id': non_existent_book_id}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_book_not_reserved_by_user(self):
        """
        Test that a user cannot return a book they did not reserve
        """
        self.client.force_authenticate(user=self.user2)
        url = reverse('return_book', args=[self.book.book_id])
        data = {'reservation_id': self.reservation.reservation_id}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'You do not have permission to return this book.',
            response.data['non_field_errors'][0]
            )

    def test_return_already_returned_book(self):
        """
        Test that book that has already been returned cannot be returned again
        """
        self.client.force_authenticate(user=self.user1)
        url = reverse('return_book', args=[self.book.book_id])
        data = {'reservation_id': self.reservation.reservation_id}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'Reservation does not exist or already returned.',
            response.data['non_field_errors'][0]
            )


class UserReservationListViewTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        self.book = Book.objects.create(
            title='Test Book',
            author='Author A',
            isbn='1234567890123',
            count_in_library=10,
            library='Main Library'
        )
        self.reservation1 = Reservation.objects.create(
            user=self.user1,
            book=self.book,
            reserved_until=datetime.now() + timedelta(days=30),
            reservation_status=True,
            reservation_library=self.book.library,
            is_external=False
        )
        self.reservation2 = Reservation.objects.create(
            user=self.user2,
            book=self.book,
            reserved_until=datetime.now() + timedelta(days=30),
            reservation_status=True,
            reservation_library=self.book.library,
            is_external=False
        )
        self.client = APIClient()

    def test_authenticated_user_retrieves_own_reservations(self):
        """
        Test that an authenticated user can retrieve their own reservations.
        """
        self.client.force_authenticate(user=self.user1)
        url = reverse('user_reservations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_reservations = Reservation.objects.filter(user=self.user1)
        serializer = ReservationSerializer(expected_reservations, many=True)
        self.assertEqual(data, serializer.data)

    def test_unauthenticated_user_denied_access(self):
        """
        Test that an unauthenticated user cannot access the reservations list.
        """
        url = reverse('user_reservations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_only_sees_own_reservations(self):
        """
        Test that a user only sees their own reservations, not others'.
        """
        self.client.force_authenticate(user=self.user1)
        url = reverse('user_reservations')
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['user'], self.user1.username)
        self.assertEqual(data[0]['reservation_id'], self.reservation1.reservation_id)
        reservation_ids = [reservation['reservation_id'] for reservation in data]
        self.assertNotIn(self.reservation2.reservation_id, reservation_ids)


class UserRegistrationViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('user_register')

    def test_user_registration_success(self):
        """
        Test that a user can register successfully with valid data
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPassw0rd!',
            'password_confirm': 'StrongPassw0rd!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'User registered successfully')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_registration_missing_fields(self):
        """
        Test that registration fails when required fields are missing
        """
        data = {
            'username': 'newuser',
            'password': 'StrongPassw0rd!',
            # 'password_confirm' is missing
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_user_registration_passwords_do_not_match(self):
        """
        Test that registration fails when passwords do not match
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPassw0rd!',
            'password_confirm': 'DifferentPassword!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertEqual(response.data['password'][0], "Password fields didn't match.")

    def test_user_registration_existing_username(self):
        """
        Test that registration fails when the username already exists
        """
        User.objects.create_user(username='existinguser', password='password123')
        data = {
            'username': 'existinguser',
            'email': 'newuser@example.com',
            'password': 'StrongPassw0rd!',
            'password_confirm': 'StrongPassw0rd!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_user_registration_invalid_email(self):
        """
        Test that registration fails when the email format is invalid
        """
        data = {
            'username': 'newuser',
            'email': 'invalidemail',
            'password': 'StrongPassw0rd!',
            'password_confirm': 'StrongPassw0rd!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_registration_weak_password(self):
        """
        Test that registration fails when the password does not meet validation criteria
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'weak',
            'password_confirm': 'weak'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class ReservationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.book_available = Book.objects.create(
            title='Available Book',
            author='Author A',
            isbn='1111111111111',
            count_in_library=5,
            library='Main Library'
        )
        self.book_not_available = Book.objects.create(
            title='Unavailable Book',
            author='Author B',
            isbn='2222222222222',
            count_in_library=0,
            library='Main Library'
        )
        self.client = APIClient()

    @patch('app.views.AvailabilityService')
    def test_reserve_book_main_library(self, mock_availability_service):
        """
        Test reserving a book that is available in the main library
        """
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer testtoken')
        url = reverse('reserve_book', args=[self.book_available.book_id])
        data = {
            'book_id': self.book_available.book_id,
        }
        response = self.client.post(url, data, format='json')
        # response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        reservation = Reservation.objects.first()
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.book, self.book_available)
        self.assertFalse(reservation.is_external)
        self.assertEqual(reservation.reservation_library, self.book_available.library)
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.count_in_library, 4)

    @patch('app.views.AvailabilityService')
    def test_reserve_book_external_library(self, mock_availability_service):
        """
        Test reserving a book that is not available in \
            the main library but is available externally
        """
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer testtoken')
        url = reverse('reserve_book', args=[self.book_not_available.book_id])

        data = {
            'book_id': self.book_not_available.book_id,
        }
        mock_service = mock_availability_service.return_value
        mock_external_availability = {
            '3': {  # Simulating external book ID
                'library': 'External Library',
                'count_in_library': 2
            }
        }
        mock_service.check_book_availability_flask.return_value = mock_external_availability
        mock_service.reserve_book_external_api.return_value = True
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        reservation = Reservation.objects.first()
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.book, self.book_not_available)
        self.assertTrue(reservation.is_external)
        self.assertEqual(reservation.reservation_library, 'External Library')
        self.book_not_available.refresh_from_db()
        self.assertEqual(self.book_not_available.count_in_library, 0)
        mock_service.check_book_availability_flask.assert_called_once_with(
            self.book_not_available.isbn
            )
        mock_service.reserve_book_external_api.assert_called_once_with('3', 'testtoken')

    @patch('app.views.AvailabilityService')
    def test_reserve_book_not_available_anywhere(self, mock_availability_service):
        """
        Test attempting to reserve a book that is not available in the main or external libraries
        """
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer testtoken')
        url = reverse('reserve_book', args=[self.book_not_available.book_id])

        data = {
            'book_id': self.book_not_available.book_id,
        }
        mock_service = mock_availability_service.return_value
        mock_service.check_book_availability_flask.return_value = False
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('This book is not available', str(response.data[0]))
        self.assertEqual(Reservation.objects.count(), 0)
        mock_service.check_book_availability_flask.assert_called_once_with(
            self.book_not_available.isbn
        )
        mock_service.reserve_book_external_api.assert_not_called()

    def test_reserve_book_not_authenticated(self):
        """
        Test that an unauthenticated user cannot reserve a book
        """
        url = reverse('reserve_book', args=[self.book_available.book_id])
        data = {
            'book_id': self.book_available.book_id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_reserve_nonexistent_book(self):
        """
        Test attempting to reserve a book that does not exist
        """
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer testtoken')
        non_existent_book_id = 999
        url = reverse('reserve_book', args=[non_existent_book_id])
        data = {
            'book_id': non_existent_book_id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid pk', str(response.data))
        self.assertEqual(Reservation.objects.count(), 0)
