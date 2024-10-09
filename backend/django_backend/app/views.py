import logging
import asyncio
from rest_framework import status, permissions, generics, mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from django.contrib.auth.models import User
from services.book_availability_service import AvailabilityService
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from app.models import Book, Reservation
from app.utils import cache_api_view
from app.serializers import (
    BookSerializer,
    ReservationSerializer,
    # UserSerializer,
    UserRegistrationSerializer,
    ReturnBookSerializer)

# Get an instance of a logger
logger = logging.getLogger(__name__)


class BookViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """Book view accessible to all users.
    Defines check_availability and search_by_isbn.
    """
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        description="List all books. This list is cached, invalidation is supported by signals",
        responses={200: BookSerializer(many=True)}
    )
    @cache_api_view('books_list', 60 * 5)
    def list(self, request, *args, **kwargs):
        """List all books. This list is cached, invalidation is also supported by signals"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description="Check availability of a book in internal and external libraries",
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Successful Response',
                value={
                    'book_title': 'Sample Book',
                    'author': 'John Doe',
                    'isbn': '1234567890',
                    'local_library_network_availability': [
                        {'book_id': 1, 'library': 'Main Library', 'count_in_library': 2},
                        {'book_id': 2, 'library': 'Main Library', 'count_in_library': 3}
                    ],
                    'external_availability': {
                        1: {'count_in_library': 1, 'library': 'External Library A'},
                        4: {'count_in_library': 3, 'library': 'External Library B'}
                        }
                }
            )
        ]
    )
    @action(detail=True, methods=['get'])
    def check_availability(self, request, pk=None):
        """To search for a book in external libraries, it must be defined by ORM
        for proper ISBN enumeration
        """
        try:
            # book = await asyncio.to_thread(self.get_object)
            book = self.get_object()
            availability_service = AvailabilityService()

            # Check availability in external libraries
            external_availability = availability_service.check_book_availability_flask(book.isbn)

            # Check availability across different objects based on ISBN
            local_library_network = Book.objects.filter(isbn=book.isbn)
            if local_library_network:
                local_availability_data = [
                        {
                            'book_id': book.book_id,
                            'library': book.library,
                            'count_in_library': book.count_in_library
                        } for book in local_library_network
                ]

            availability_data = {
                'book_title': book.title,
                'author': book.author,
                'isbn': book.isbn,
                'local_library_network_availability': local_availability_data,
                'external_availability': external_availability,
            }
            return Response(availability_data)
        except Exception as e:
            logger.error(f"Error while checking external availability': {str(e)}")
            raise ValidationError(
                "An error occurred while checking internal and external availability")

    @extend_schema(
        description="Search for a book by ISBN",
        parameters=[
            OpenApiParameter(name='isbn', description='ISBN of the book', required=True, type=str)
        ],
        responses={
            200: BookSerializer(many=True),
            400: OpenApiTypes.OBJECT
        }
    )
    @action(detail=False, methods=['get'])
    def search_by_isbn(self, request):
        """Search internally for a book based on ISBN.
        """
        isbn = request.query_params.get('isbn', None)

        if isbn is None:
            return Response({"error": "Please provide correct ISBN"}, status=400)

        books = self.queryset.filter(isbn=isbn)  # Already as str

        if len(books) < 1:
            return Response({"error": "No books found with provided ISBN"}, status=400)

        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)


class ReturnBookView(generics.UpdateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReturnBookSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Return a book",
        request=ReturnBookSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Successful Response',
                value={'status': 'Book returned successfully'}
            )
        ]
    )
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Get the reservation instance and update it
        reservation = Reservation.objects.get(
            reservation_id=serializer.validated_data['reservation_id']
            )
        self.perform_update(serializer, reservation)

        return Response({"status": "Book returned successfully"}, status=status.HTTP_200_OK)

    def perform_update(self, serializer, instance):
        # Using the serializer to update the reservation instance
        logger.info(f"Updating reservation instance ID: {instance.reservation_id}")
        serializer.update(instance=instance, validated_data=serializer.validated_data)


class BookListCreateView(generics.RetrieveUpdateDestroyAPIView,
                         generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        description="List all books or create a new book",
        responses={
            200: BookSerializer(many=True),
            201: BookSerializer,
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        description="Create a new book",
        request=BookSerializer,
        responses={201: BookSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserReservationListView(generics.ListAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="List all reservations for the current user",
        responses={200: ReservationSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)


class ReserveBookView(generics.CreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Reserve a book",
        request=ReservationSerializer,
        responses={
            201: ReservationSerializer,
            400: OpenApiTypes.OBJECT
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def extract_jwt_token(self):
        auth_header = self.request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            raise ValueError("Missing Authorization header")

        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                raise ValueError("Invalid Authorization header format")
            return token
        except ValueError:
            raise ValueError("Invalid Authorization header format")

    def perform_create(self, serializer):
        book = serializer.validated_data['book']
        availability_service = AvailabilityService()
        logger.info(f"User is attempting to reserve book: {book.isbn}")

        try:
            token = self.extract_jwt_token()
            # Apply certain logic: if book is not available in the main library,
            #   then check external ones, and if is available continue with respective library
            if book.count_in_library < 1:
                # Check the availability from the external system using the service
                external_availability = availability_service.check_book_availability_flask(book.isbn)

                # Check book in external libraries
                if not external_availability:
                    raise ValidationError("This book is not available in the \
                                        internal and external library system.")

                # Select book PK from external API, currently uses the first on the list
                #   API returns libraries with count of books > 0 in libraries
                selected_book_external_pk, availability_details = list(external_availability.items())[0]

                if not availability_details['count_in_library'] > 0:
                    # TODO logging here
                    raise ValidationError("Unexpected error, only available books from \
                                        external API should be received.")

                reservation_library = availability_details['library']
                # Reserve book via Flask endpoint (count - 1)
                availability_service.reserve_book_external_api(selected_book_external_pk, token)
                is_external = True

            else:
                # Process with a 'Main Library'
                reservation_library = book.library
                # Decrease the available copies count and create the reservation
                book.count_in_library -= 1
                book.save()
                is_external = False

            if serializer.is_valid():
                serializer.save(
                    user=self.request.user,
                    reservation_library=reservation_library,
                    is_external=is_external,
                    )
        except ValidationError as e:
            logger.error(f"Validation error while reserving book '{book.title}': {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error while reserving book '{book.title}': {str(e)}")
            raise ValidationError("An error occurred while reserving the book")


class UserRegistrationView(generics.CreateAPIView):
    """
    View for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        description="Register a new user",
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Successful Response',
                value={'status': 'User registered successfully'}
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        logger.info("User registration attempt")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info(f"User registered successfully: {user.username}")
        return Response(
            {"status": "User registered successfully"},
            status=status.HTTP_201_CREATED
        )
