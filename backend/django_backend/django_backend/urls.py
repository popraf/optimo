from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView,
                                            TokenBlacklistView)
from app.views import UserRegistrationView


urlpatterns = [
     path('admin/', admin.site.urls),
     path('api/', include('app.urls')),
     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
     path('api/register/', UserRegistrationView.as_view(), name='user_register'),
     path('api/logout/', TokenBlacklistView.as_view(), name='user_logout'),
]
