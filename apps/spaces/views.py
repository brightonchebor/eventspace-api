from django.shortcuts import render
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Space
from .serializers import SpaceSerializer

class CreateSpaceView(CreateAPIView):
    """
    Create a new space
    """
    serializer_class = SpaceSerializer
    queryset = Space.objects.all()

    @swagger_auto_schema(
        operation_summary='Create a new space',
        operation_description='Create a new event space with the provided details',
        request_body=SpaceSerializer,
        responses={
            201: openapi.Response(
                description='Space created successfully',
                schema=SpaceSerializer
            ),
            400: openapi.Response(
                description='Bad request - validation errors',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if 'image' in request.data:
            images = request.data.get('image', [])
            if len(images) > 5:
                return Response({
                    'message': 'Failed to create space',
                    'errors': {
                        'image': ['You can only upload a maximum of 5 images per space.']
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        
        if serializer.is_valid():
            space = serializer.save()
            return Response({
                'message': f'Space "{space.name}" has been created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'message': 'Failed to create space',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class ListSpacesView(ListAPIView):
    """
    List all spaces
    """
    serializer_class = SpaceSerializer
    queryset = Space.objects.all()

    @swagger_auto_schema(
        operation_summary='List all spaces',
        operation_description='Get a list of all available event spaces',
        responses={
            200: openapi.Response(
                description='List of spaces retrieved successfully',
                schema=SpaceSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
