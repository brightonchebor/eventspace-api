from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Space
from .serializers import SpaceSerializer, SpaceDeleteSerializer

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

@api_view(['GET'])
@permission_classes([AllowAny])
def list_spaces(request):
    """
    List all available spaces
    """
    spaces = Space.objects.all()
    serializer = SpaceSerializer(spaces, many=True)
    return Response(serializer.data)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve details of a space by its ID.",
    responses={200: SpaceSerializer(), 404: 'Not Found'}
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def space_detail(request, pk):
    """
    Retrieve details of a space by its ID.
    """
    try:
        space = Space.objects.get(pk=pk)
    except Space.DoesNotExist:
        return Response({"error": "Space not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = SpaceSerializer(space)
    return Response(serializer.data)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve images for a specific space by ID.",
    responses={200: 'List of space images', 404: 'Not Found'}
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def space_images(request, pk):
    """
    Retrieve images for a specific space by ID.
    """
    try:
        space = Space.objects.get(pk=pk)
    except Space.DoesNotExist:
        return Response({"error": "Space not found"}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='delete',
    operation_summary='Delete a space',
    operation_description='Delete a space by its ID.',
    responses={
        204: openapi.Response(description='Space deleted successfully'),
        404: openapi.Response(description='Space not found')
    }
)
@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])

def delete_space(request, pk):
    """
    Delete a space by its ID.
    """
    serializer = SpaceDeleteSerializer(data={"id": pk})
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    try:
        space = Space.objects.get(pk=serializer.validated_data["id"])
    except Space.DoesNotExist:
        return Response({"error": "Space not found"}, status=status.HTTP_404_NOT_FOUND)
    space.delete()
    return Response({"message": "Space deleted successfully."}, status=status.HTTP_200_OK)




