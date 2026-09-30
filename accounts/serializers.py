from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Expose the signed-in user's profile without ever returning their password."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "phone_number")
        read_only_fields = ("id",)


class RegistrationSerializer(serializers.ModelSerializer):
    """Create a customer account; a valid response contains only safe profile fields."""

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "phone_number", "password")
        read_only_fields = ("id",)

    def create(self, validated_data):
        # set_password hashes the credential; a successful response never contains it.
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Validate username and password; invalid credentials return a field error."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if user is None or not user.is_active:
            raise serializers.ValidationError({"detail": "Invalid username or password."})
        attrs["user"] = user
        return attrs
