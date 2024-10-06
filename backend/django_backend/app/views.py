import logging
from rest_framework import status, permissions, generics, mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from django.contrib.auth.models import User
from services.book_availability_service import AvailabilityService
from .models import Book, Reservation
from .serializers import (
    BookSerializer,
    ReservationSerializer,
    # UserSerializer,
    UserRegistrationSerializer)

# Get an instance of a logger
logger = logging.getLogger(__name__)


class BookViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    """
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['get'])
    def check_external_availability(self, request, pk=None):
        book = self.get_object()
        availability_service = AvailabilityService()
        # Check availability in external libraries
        external_availability = availability_service.check_book_availability_flask(book.isbn)
        # Check availability across different objects based on ISBN
        local_library_network = Book.objects.filter(book.isbn)
        local_availability_data = {
                {
                    'book_id': book['book_id'],
                    book['library']: book['count_in_library']
                } for book in local_library_network
            }
        availability_data = {
            'book_title': book.title,
            'author': book.author,
            'isbn': book.isbn,
            'local_library_network_availability': local_availability_data,
            'external_availability': external_availability,
        }
        return Response(availability_data)

    @action(detail=False, methods=['get'])
    def search_by_isbn(self, request):
        isbn = request.query_params.get('isbn', None)
        if isbn is not None:
            books = self.queryset.filter(isbn=isbn)
            serializer = self.get_serializer(books, many=True)
            return Response(serializer.data)
        return Response({"error": "Please provide an ISBN"}, status=400)


class BookListCreateView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAdminUser]


class UserReservationListView(generics.ListAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)


class ReserveBookView(generics.CreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        book = serializer.validated_data['book']
        availability_service = AvailabilityService()

        # Apply certain logic: if book is not available in the main library,
        #   then check external ones, and if is available continue with respective library
        if book.count_in_library < 1:
            # Check the availability from the external system using the service
            external_availability = availability_service.check_book_availability_flask(book.isbn)

            # Check book in external libraries
            if not external_availability:
                raise ValidationError("This book is not available in the \
                                    internal and external library system.")

            # Select book PK from external API, currently uses the first on the list that is > 0
            selected_pk = external_availability['pk']
            # TODO fix according to flask
            external_library_details = availability_service.get_book_details(selected_pk)
            reservation_library = external_library_details['library']
            # Reserve book via Flask endpoint (count - 1)
            availability_service.reserve_book_external_api(book.isbn)
            is_external = True

        else:
            # Process with a 'Main Library'
            reservation_library = book.library
            # Decrease the available copies count and create the reservation
            book.count_in_library -= 1
            book.save()
            is_external = False

        # Create the reservation with user and book
        serializer.save(
            user=self.request.user,
            reservation_library=reservation_library,
            is_external=is_external)


class UserRegistrationView(generics.CreateAPIView):
    """
    View for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

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
