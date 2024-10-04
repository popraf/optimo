from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Book, Reservation
from .serializers import BookSerializer, ReservationSerializer
from django.contrib.auth.models import User
from django.conf import settings
import requests


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    @action(detail=True, methods=['post'])
    def reserve(self, request, pk=None):
        book = self.get_object()
        user = request.user

        # Check availability via Flask API
        flask_api_url = f"http://flask:5000/status/{book.external_id}"
        try:
            response = requests.get(flask_api_url)
            response.raise_for_status()
            data = response.json()
            if data.get('available'):
                reservation = Reservation.objects.create(user=user, book=book, status='reserved')
                serializer = ReservationSerializer(reservation)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Book not available'}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException:
            return Response({'error': 'Failed to connect to Flask API'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
