from django.shortcuts import render
from .serializers import *
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .utils import send_code_to_user
from .models import OneTimePassword, User


from rest_framework.permissions import IsAuthenticated
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.exceptions import NotFound


class UserRegisterView(GenericAPIView):
    """
    User Registration API
    
    Allows new users to register by providing email, first name, last name, and password.
    After successful registration, an OTP is sent to the user's email for verification.
    """
    serializer_class = UserRegisterSerializer

    @swagger_auto_schema(
        operation_summary='Register a new user account',
        operation_description="""
        Creates a new user account with the provided information.
        
        **Process:**
        1. Validates the provided user data
        2. Creates a new user account (unverified)
        3. Sends an OTP to the user's email for verification
        4. Returns success message with user's first name
        
        **Note:** The user account will be created but marked as unverified until email verification is completed.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='User email address (must be unique)',
                    example='user@example.com'
                ),
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User first name',
                    example='John'
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User last name',
                    example='Doe'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='User password (minimum 6 characters)',
                    example='securepassword123'
                ),
                'password_confirm': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='Password confirmation (must match password)',
                    example='securepassword123'
                ),
            },
            required=['email', 'first_name', 'last_name', 'password', 'password_confirm']
        ),
        responses={
            201: openapi.Response(
                description='User registered successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Success message with user name and instructions',
                            example='Hi John thanks for signing up, a passcode has been sent to your email'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description='Bad Request - Validation errors',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description='Email validation errors',
                            example=['user with this email address already exists.']
                        ),
                        'password': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description='Password validation errors',
                            example=['passwords do not match']
                        ),
                        'non_field_errors': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description='General validation errors',
                            example=['passwords do not match']
                        )
                    }
                )
            )
        },
        tags=['Authentication']
    )
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
    

class LoginUserView(GenericAPIView):
    """
    User Login API
    
    Authenticates users and returns JWT tokens for accessing protected endpoints.
    """
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        operation_summary='Login user and get JWT tokens',
        operation_description="""
        Authenticates a user with email and password, returning JWT tokens for API access.
        
        **Process:**
        1. Validates user credentials (email and password)
        2. Checks if user account is verified
        3. Generates and returns JWT access and refresh tokens
        4. Returns user information along with tokens
        
        **Requirements:**
        - User must have verified their email address
        - Valid email and password combination
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='User email address',
                    example='user@example.com'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='User password',
                    example='securepassword123'
                ),
            },
            required=['email', 'password']
        ),
        responses={
            200: openapi.Response(
                description='Login successful',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_EMAIL,
                            description='User email address',
                            example='user@example.com'
                        ),
                        'full_name': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='User full name',
                            example='John Doe'
                        ),
                        'access_token': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT access token for API authentication',
                            example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                        ),
                        'refresh_token': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='JWT refresh token for obtaining new access tokens',
                            example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                        ),
                    }
                )
            ),
            401: openapi.Response(
                description='Authentication failed',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message',
                            example='invalid credentials try again'
                        )
                    }
                )
            ),
            403: openapi.Response(
                description='Email not verified',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message',
                            example='email is not verified'
                        )
                    }
                )
            )
        },
        tags=['Authentication']
    )
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
    """
    Email Verification API
    
    Verifies user email address using OTP sent during registration.
    """

    @swagger_auto_schema(
        operation_summary='Verify user email with OTP',
        operation_description="""
        Verifies a user's email address using the OTP (One-Time Password) sent during registration.
        
        **Process:**
        1. Validates the provided OTP code
        2. Marks the user account as verified
        3. Enables the user to login
        
        **Note:** Each OTP can only be used once and expires after a certain time.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='6-digit One-Time Password sent to user email',
                    example='123456',
                    minLength=6,
                    maxLength=6
                ),
            },
            required=['otp']
        ),
        responses={
            200: openapi.Response(
                description='Email verified successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Success message',
                            example='email account verified successfully'
                        )
                    }
                )
            ),
            204: openapi.Response(
                description='User already verified',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Status message',
                            example='code is invalid user already exist'
                        )
                    }
                )
            ),
            404: openapi.Response(
                description='Invalid OTP',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message',
                            example='passcode not provided'
                        )
                    }
                )
            )
        },
        tags=['Authentication']
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
    """
    Password Reset Request API
    
    Initiates password reset process by sending reset link to user's email.
    """
    serializer_class = PasswordResetRequestSerializer

    @swagger_auto_schema(
        operation_summary='Request password reset',
        operation_description="""
        Initiates the password reset process by sending a reset link to the user's email.
        
        **Process:**
        1. Validates if the email exists in the system
        2. Generates a secure reset token
        3. Sends password reset link to user's email
        4. Returns success message
        
        **Note:** If the email doesn't exist, no error is returned for security reasons.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='User email address',
                    example='user@example.com'
                ),
            },
            required=['email']
        ),
        responses={
            200: openapi.Response(
                description='Password reset email sent',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Success message',
                            example='a link has been sent to your email to reset your password'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description='Validation errors',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description='Email validation errors',
                            example=['Enter a valid email address.']
                        )
                    }
                )
            )
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request':request})    
        serializer.is_valid(raise_exception=True)
        return Response({
            'message':'a link has been sent to your email to reset your password'
        }, status=status.HTTP_200_OK)            


class PasswordResetConfirm(GenericAPIView):
    """
    Password Reset Confirmation API
    
    Validates password reset token from email link.
    """
    
    @swagger_auto_schema(
        operation_summary='Confirm password reset token',
        operation_description="""
        Validates the password reset token received from the email link.
        
        **Process:**
        1. Decodes the user ID from the URL
        2. Validates the reset token
        3. Returns success if token is valid
        
        **URL Parameters:**
        - uidb64: Base64 encoded user ID
        - token: Password reset token
        """,
        manual_parameters=[
            openapi.Parameter(
                'uidb64',
                openapi.IN_PATH,
                description='Base64 encoded user ID',
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'token',
                openapi.IN_PATH,
                description='Password reset token',
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description='Token is valid',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description='Success status',
                            example=True
                        ),
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Success message',
                            example='credentials are valid'
                        ),
                        'uidb64': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Base64 encoded user ID',
                            example='MjM'
                        ),
                        'token': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Password reset token',
                            example='abc123-def456-ghi789'
                        ),
                    }
                )
            ),
            401: openapi.Response(
                description='Invalid or expired token',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message',
                            example='token is invalid or has expired'
                        )
                    }
                )
            )
        },
        tags=['Authentication']
    )
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
    """
    Set New Password API
    
    Sets a new password after successful token validation.
    """
    serializer_class = SetNewPasswordSerializer

    @swagger_auto_schema(
        operation_summary='Set new password',
        operation_description="""
        Sets a new password for the user after validating the reset token.
        
        **Process:**
        1. Validates the reset token and user credentials
        2. Ensures password confirmation matches
        3. Updates the user's password
        4. Returns success message
        
        **Note:** The token and uidb64 should be obtained from the password reset confirmation step.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='New password (minimum 6 characters)',
                    example='newsecurepassword123'
                ),
                'password_confirm': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='Password confirmation (must match password)',
                    example='newsecurepassword123'
                ),
                'uidb64': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Base64 encoded user ID from reset link',
                    example='MjM'
                ),
                'token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Password reset token from reset link',
                    example='abc123-def456-ghi789'
                ),
            },
            required=['password', 'password_confirm', 'uidb64', 'token']
        ),
        responses={
            200: openapi.Response(
                description='Password reset successful',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Success message',
                            example='password reset successful'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description='Validation errors',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'password': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description='Password validation errors',
                            example=['password does not match']
                        ),
                        'non_field_errors': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description='General validation errors',
                            example=['reset link is invalid or has expired']
                        )
                    }
                )
            ),
            401: openapi.Response(
                description='Invalid or expired token',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message',
                            example='reset link is invalid or has expired'
                        )
                    }
                )
            )
        },
        tags=['Authentication']
    )
    def patch(self, request): # we are updatinng the pwd
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'message':'password reset successful'
        }, status=status.HTTP_200_OK)


class LogoutUserView(GenericAPIView):
    """
    User Logout API
    
    Logs out authenticated users by blacklisting their refresh token.
    """
    serializer_class = LogoutUsererializer    
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary='Logout user',
        operation_description="""
        Logs out an authenticated user by blacklisting their refresh token.
        
        **Process:**
        1. Validates the refresh token
        2. Adds the token to the blacklist
        3. Prevents further use of the token
        
        **Authentication Required:** This endpoint requires a valid JWT access token.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='JWT refresh token to blacklist',
                    example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                ),
            },
            required=['refresh_token']
        ),
        responses={
            204: openapi.Response(
                description='Successfully logged out'
            ),
            400: openapi.Response(
                description='Invalid refresh token',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh_token': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description='Token validation errors',
                            example=['Token is invalid or has expired']
                        )
                    }
                )
            ),
            401: openapi.Response(
                description='Authentication required',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message',
                            example='Authentication credentials were not provided.'
                        )
                    }
                )
            )
        },
        tags=['Authentication'],
        security=[{'Bearer': []}]
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)