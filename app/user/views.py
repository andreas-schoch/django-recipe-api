from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework import generics

from user.serielizers import UserSerielizer, AuthTokenSerializer


class CreateUserView(generics.CreateAPIView):
    """Create new user in the system"""
    serializer_class = UserSerielizer


class CreateTokenView(ObtainAuthToken):
    """Create new auth token for user"""
    serializer_class = AuthTokenSerializer
    # makes it possible to view endpoint via the browsable api, no need to use postman etc.
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
