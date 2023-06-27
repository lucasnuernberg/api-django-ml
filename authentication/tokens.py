
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from .serielizers import CustomTokenRefreshSerializer , CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshViewPairView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


