from django.shortcuts import render
from .serializers import UserRegisterSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .utils import send_code_to_user
from .models import OneTimePassword

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

class VerifyUserEmail(GenericAPIView):

    @swagger_auto_schema(operation_summary='Confirming password reset.',request_body=openapi.Schema(
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