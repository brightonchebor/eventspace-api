from django.shortcuts import render
from .serializers import UserRegisterSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

class UserRegisterView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    @swagger_auto_schema(operation_summary='Register a user.')
    def post(self, request):
        user_data = request.data
        
        serializer = self.serializer_class(data=user_data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            user = serializer.data
            # send_code_to_user(user['email'])
            # send email function user['email']
            return Response({
                'message':f'hi {user["first_name"]} thanks for signing up, a passcode has been sent to your email',
              }, status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
