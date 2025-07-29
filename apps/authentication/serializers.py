from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_str, smart_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import send_normal_email
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema 


class UserRegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password_confirm = serializers.CharField(max_length=68, min_length=6, write_only=True)

    class Meta:

        model = User
        fields = ['id','email', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate(self, attr):

        password = attr.get('password', '')
        password_confirm = attr.get('password_confirm', '')
        if password != password_confirm:
            raise serializers.ValidationError('passwords do not match')
        return attr

    def create(self, validated_data):
        
        user = User.objects.create_user(
            email = validated_data['email'],
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            password = validated_data['password']
        )
        return user
    
class LoginSerializer(serializers.Serializer):
    id            = serializers.IntegerField(read_only=True)
    full_name     = serializers.CharField(read_only=True)
    role          = serializers.CharField(read_only=True)
    access_token  = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    email    = serializers.EmailField(write_only=True, max_length=255)
    password = serializers.CharField(write_only=True, max_length=128)

    def validate(self, attrs):
        email    = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )

        if not user:
            raise AuthenticationFailed("Invalid credentials, try again.")
        if not user.is_verified:
            raise AuthenticationFailed("Email is not verified.")

        # Generate JWT tokens
        tokens = user.tokens()

        return {
            'id':            user.pk,
            'full_name':     user.get_full_name,
            'role':          user.role,
            'access_token':  tokens['access'],
            'refresh_token': tokens['refresh'],
        }

    def to_representation(self, validated_data):
        # Simply return exactly what validate() returned
        return validated_data

class PasswordResetRequestSerializer(serializers.Serializer):
    email =serializers.EmailField(max_length=255)

    class Meta:
        fields = ['email']

    def validate(self, attrs):
        email = attrs.get('email') 
        if User.objects.filter(email=email).exists(): # check if user is in the database
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            request = self.context.get('request')
            # site_domain = get_current_site(request).domain
            site_domain = "localhost:5173"
            relative_link = reverse('password-reset-confirm', kwargs={
                'uidb64':uidb64,
                'token':token
            })
            abslink = f'http://{site_domain}{relative_link}'
            email_body = f'Hi use the link below to reset your email \n {abslink}'
            data = {
                'email_body':email_body,
                'email_subject':'reset your password',
                'to_email':user.email
            }
            send_normal_email(data)
        return super().validate(attrs)   
# http://localhost:5173/password-reset-confirm/MQ/ctadwo-f74800b67dcf04d02d9b57fa7d57957e/
class  SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    password_confirm = serializers.CharField(max_length=100, min_length=6, write_only=True)
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    class Meta:
        fields = ['password', 'password_confirm', 'uidb64', 'token']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            password_confirm = attrs.get('password_confirm')
            uidb64 = attrs.get('uidb64')
            token = attrs.get('token')

            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('reset link is invalid or has expired', 401)
            if password != password_confirm:
                raise AuthenticationFailed('password does not match')
        
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            return AuthenticationFailed('link is invalid or has expired') 


class LogoutUsererializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    default_error_message = {
        'key':('Token is invalid or has expired')
    }

    def validate(self, attrs):
        self.token = attrs.get('refresh_token')

        return attrs
    def save(self, **kwarags):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail('bad_token')                          

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user objects"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name']
        read_only_fields = ['id']