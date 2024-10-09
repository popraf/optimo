from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView,
                                            TokenBlacklistView,
                                            TokenVerifyView)
from app.views import UserRegistrationView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
     path('admin/', admin.site.urls),
     path('api/', include('app.urls')),
     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
     path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
     path('api/register/', UserRegistrationView.as_view(), name='user_register'),
     path('api/logout/', TokenBlacklistView.as_view(), name='user_logout'),

     path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
     path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
     path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
