from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    BookViewSet,
    BookListCreateView,
    UserReservationListView,
    ReserveBookView,
    ReturnBookView,
    )


router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')

urlpatterns = [
    # List and create book entries (Admin only)
    path('books/manage/', BookListCreateView.as_view(), name='book_list_create'),

    # Get list of reservations for a specific user (User only)
    path('reservations/', UserReservationListView.as_view(), name='user_reservations'),

    # Reserve a book (User only)
    path('reserve/<int:book_id>/', ReserveBookView.as_view(), name='reserve_book'),

    # Return a book
    path('return/<int:book_id>/', ReturnBookView.as_view(), name='return_book'),
    ]
urlpatterns += router.urls
