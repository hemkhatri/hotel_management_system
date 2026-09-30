from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserModel

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number')
        read_only_fields = ('id',)

class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 'password')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'validators': [validate_password],
            }
        }
    def create(self, validate_data):
        return UserModel.objects.create_user(**validate_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only = True, trim_whitespace = False)

    def validate(self, attrs):
        user = authenticate(username = attrs['username'], password = attrs['password'])
        if user is None or not user.is_active:
            raise serializers.ValidationError({'detail': 'Invalid username or password'})
        attrs['user'] = user
        return attrs