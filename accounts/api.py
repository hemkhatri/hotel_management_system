from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Register a customer; HTTP 201 means the account was created successfully."""

    serializer_class = RegistrationSerializer
    permission_classes = (permissions.AllowAny,)


class LoginView(APIView):
    """Issue a reusable API token; HTTP 200 includes the token for valid credentials.  """

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token, _ = Token.objects.get_or_create(user=serializer.validated_data["user"])
        return Response({"token": token.key, "user": UserSerializer(serializer.validated_data["user"]).data})


class LogoutView(APIView):
    """Delete the current token; HTTP 204 means this token can no longer authenticate."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """Read or update only the authenticated user's profile; success returns safe profile data."""

    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        # Returning request.user prevents callers from changing another user's profile by ID.
        return self.request.user
