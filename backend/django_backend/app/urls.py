from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, ReservationViewSet
from rest_framework.authtoken import views

router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'reservations', ReservationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', views.obtain_auth_token),
]
