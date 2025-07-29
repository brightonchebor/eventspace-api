from django.shortcuts import render
from .serializers import *
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .utils import send_code_to_user
from .models import OneTimePassword, User
from rest_framework.permissions import IsAdminUser


from rest_framework.permissions import IsAuthenticated
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.exceptions import NotFound


class UserRegisterView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    @swagger_auto_schema(operation_summary='Register a user.')
    def post(self, request):
        user_data = request.data
        
        serializer = self.serializer_class(data=user_data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            user = serializer.data
            send_code_to_user(user['email'])
            # send email function user['email']
            return Response({
                'message':f'Hi {user["first_name"]} thanks for signing up, a passcode has been sent to your email',
              }, status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginUserView( GenericAPIView):
    serializer_class = LoginSerializer

    @swagger_auto_schema(operation_summary='Login user to get generate JWT token.')
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={
                'request':request
            }
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
class VerifyUserEmail(GenericAPIView):

    @swagger_auto_schema(operation_summary='Verifying account using OTP sent to email',request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description='One-Time Password (OTP) sent to user email'),
            },
            required=['otp'],  # Marking 'otp' as a required field
        ),responses={
            200: openapi.Response(
                description='Email verified successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            )}
        )
    def post(self, request):
        otpcode = request.data.get('otp')
        try:
            user_code_obj = OneTimePassword.objects.get(code=otpcode)
            user = user_code_obj.user
            if not user.is_verified:
                user.is_verified = True
                user.save()
                return Response({
                    'message':'email account verified successfully'
                }, status=status.HTTP_200_OK)
            return Response({
                'message':'code is invalid user already exist'
            }, status=status.HTTP_204_NO_CONTENT)

        except OneTimePassword.DoesNotExist:
            return Response({
                'message':'passcode not provided'
            }, status=status.HTTP_404_NOT_FOUND)

class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    @swagger_auto_schema(operation_summary='Request for a password reset.')
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request':request})    
        serializer.is_valid(raise_exception=True)
        return Response({
            'message':'a link has been sent to your email to reset your password'
        }, status=status.HTTP_200_OK)            


class PasswordResetConfirm(GenericAPIView):
    
    @swagger_auto_schema(operation_summary='Confirm Password.')
    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({
                    'message':'token is invalid or has expired'
                }, status=status.HTTP_401_UNAUTHORIZED)
            return Response({
                'success':True,
                'message':'credentials are valid',
                'uidb64':uidb64,
                'token':token,
            }, status=status.HTTP_200_OK)
        except DjangoUnicodeDecodeError:
            return Response({
                'message':'token is invalid or has expired'
            }, status=status.HTTP_401_UNAUTHORIZED)


class SetNewPassword(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    @swagger_auto_schema(operation_summary='Set new password.')
    def patch(self, request): # we are updatinng the pwd
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'message':'password reset successful'
        }, status=status.HTTP_200_OK)

class LogoutUserView(GenericAPIView):
    serializer_class = LogoutUsererializer    
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(operation_summary='Log out a user.')
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT) 
         
class DeleteAllUsersView(GenericAPIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(operation_summary='Delete all users (admin only).')
    def delete(self, request):
        User.objects.all().delete()
        return Response({'message': 'All users deleted.'}, status=status.HTTP_204_NO_CONTENT)  