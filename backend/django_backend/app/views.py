import logging
import requests
from datetime import datetime, timedelta
from rest_framework import viewsets, status, permissions, generics
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from requests.exceptions import RequestException
from requests.adapters import HTTPAdapter
from django.contrib.auth.models import User
from django.utils import timezone
from urllib3.util.retry import Retry

from .models import Book, Reservation
from .serializers import (
    BookSerializer,
    ReservationSerializer,
    UserSerializer,
    UserRegistrationSerializer)

# Get an instance of a logger
logger = logging.getLogger(__name__)


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for performing CRUD operations on Book model.
    - Allows anyone to view books.
    - Only admin users can create, update, or delete books.
    """
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        """
        Assign permissions based on the action.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            # For create, update, partial_update, destroy actions
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class ReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for performing CRUD operations on Reservation model.
    Includes custom actions for reserving and returning a book.
    """
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # Total number of retry attempts
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        method_whitelist=["HEAD", "GET", "OPTIONS"],  # HTTP methods to retry
        backoff_factor=1  # Exponential backoff factor (e.g., 1, 2, 4 seconds)
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    @action(detail=False, methods=['post'])
    def reserve(self, request):
        """
        Custom action to reserve a book.
        Expects 'book_id' and 'reserved_until' in the request data.
        """
        logger.info("Reservation attempt by user %s", request.user.username)

        book_id = request.data.get('book_id')
        reserved_until_str = request.data.get('reserved_until')

        if not book_id or not reserved_until_str:
            logger.warning("Missing parameters in reservation request \
                           by user %s", request.user.username)
            return Response(
                {'status': 'Missing book_id or reserved_until parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            book = Book.objects.get(book_id=book_id)
            logger.debug("Book '%s' (ID: %s) found for reservation", book.title, book.book_id)
        except Book.DoesNotExist:
            logger.error("Book with book_id %s not found \
                         for user %s", book_id, request.user.username)
            return Response(
                {'status': 'Book not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Parse reserved_until date
        try:
            reserved_until = datetime.strptime(reserved_until_str, '%Y-%m-%dT%H:%M:%S')
            reserved_until = timezone.make_aware(reserved_until, timezone.get_current_timezone())
            logger.debug("'reserved_until' date parsed successfully: %s", reserved_until)
        except ValueError:
            logger.warning("Invalid 'reserved_until' format provided \
                           by user %s", request.user.username)
            return Response(
                {'status': 'Invalid reserved_until format. Use ISO 8601 format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add logic to check if 'reserved_until' does not exceed a month from today
        now = timezone.now()
        one_month_ahead = now + timedelta(days=30)
        if reserved_until > one_month_ahead:
            logger.warning("Reserved until date exceeds one month \
                           for user %s", request.user.username)
            return Response(
                {'status': 'Reservation period cannot exceed one month. \
                 Please select an earlier date.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 1: Check availability in Main Library
        main_library = 'Main Library'
        active_reservations = Reservation.objects.filter(
            book=book,
            library=main_library,
            is_reservation_finished=False,
            reserved_until__gt=now
        )

        if not active_reservations.exists():
            # Book is available in Main Library
            reservation = Reservation.objects.create(
                user=request.user,
                book=book,
                reserved_until=reserved_until,
                library=main_library
            )
            logger.info("Reservation created in Main Library \
                        for user %s: Book '%s'", request.user.username, book.title)
            serializer = self.get_serializer(reservation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Book is not available in Main Library
            logger.info("Book '%s' is not available in Main Library \
                        for user %s", book.title, request.user.username)
            # Step 2: Check availability in other libraries via Flask API
            flask_api_url = 'http://optimo-flask:8005'  # Flask service URL
            try:
                response = requests.get('%s/status/%s' % (flask_api_url, book.book_id), timeout=5)
                response.raise_for_status()
                logger.debug("Received response from Flask API for book_id %s", book.book_id)
            except RequestException as e:
                logger.exception("Error communicating with Flask API: %s", e)
                return Response(
                    {'status': 'External service error', 'detail': str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Process the response
            if response.status_code == 200:
                availability = response.json().get('availability', {})
                # Remove Main Library from availability
                availability.pop(main_library, None)
                # Find libraries where the book is available
                available_libraries = [lib for lib, is_avbl in availability.items() if is_avbl]
                if available_libraries:
                    # Book is available in another library
                    selected_library = available_libraries[0]  # Selection logic can be customized
                    reservation = Reservation.objects.create(
                        user=request.user,
                        book=book,
                        reserved_until=reserved_until,
                        library=selected_library
                    )
                    logger.info(
                        "Reservation created in %s for user %s: Book '%s'",
                        selected_library,
                        request.user.username,
                        book.title
                    )
                    serializer = self.get_serializer(reservation)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    # Book is not available in any other library
                    logger.info("Book '%s' is not available in any \
                                library for user %s", book.title, request.user.username)
                    return Response(
                        {'status': "Book is not available in any library"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                logger.error("Book with book_id %s not found in external service", book.book_id)
                return Response(
                    {'status': 'Book not found in external service'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        """
        Custom action to return a reserved book.
        """
        logger.info("Return attempt by user %s", request.user.username)

        try:
            reservation = Reservation.objects.get(pk=pk, user=request.user)
            logger.debug("Reservation %s found for return by user %s", pk, request.user.username)
        except Reservation.DoesNotExist:
            logger.error("Reservation %s not found for user %s", pk, request.user.username)
            return Response(
                {'status': 'Reservation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if reservation.is_reservation_finished:
            logger.warning("Reservation %s already marked as finished \
                           by user %s", pk, request.user.username)
            return Response(
                {'status': 'Book already returned'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set the reservation as finished
        reservation.is_reservation_finished = True
        reservation.save()
        logger.info("Reservation %s marked as finished by user %s", pk, request.user.username)
        return Response(
            {'status': 'Book returned successfully'},
            status=status.HTTP_200_OK
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for performing CRUD operations on User model.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # Override permission
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            # Only allow admin users to access these actions
            return [permissions.IsAdminUser()]
        elif self.action == 'create':
            # Allow anyone to create (though we have a separate registration view)
            return [AllowAny()]
        return super(UserViewSet, self).get_permissions()


class UserRegistrationView(generics.CreateAPIView):
    """
    View for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        logger.info("User registration attempt")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("User registered successfully: %s", user.username)
        return Response(
            {"status": "User registered successfully"},
            status=status.HTTP_201_CREATED
        )
