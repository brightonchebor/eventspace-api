from django.shortcuts import render, get_object_or_404
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework import permissions
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Space, Review
from .serializers import SpaceSerializer, ReviewSerializer, ReviewCreateSerializer

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
    
    # Continue implementing image retrieval


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    Provides CRUD operations for reviews.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Filter reviews for a specific space if space_id is provided"""
        queryset = Review.objects.all()
        space_id = self.request.query_params.get('space_id')
        if space_id:
            queryset = queryset.filter(space_id=space_id)
        return queryset
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def perform_create(self, serializer):
        """Save the user automatically when creating a review"""
        serializer.save(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Only allow users to update their own reviews"""
        review = self.get_object()
        if review.user != request.user:
            return Response(
                {"detail": "You do not have permission to edit this review."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only allow users to delete their own reviews"""
        review = self.get_object()
        if review.user != request.user:
            return Response(
                {"detail": "You do not have permission to delete this review."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


@swagger_auto_schema(
    method='get',
    operation_description="Get reviews for a specific space",
    responses={200: ReviewSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def space_reviews(request, space_id):
    """Get all reviews for a specific space"""
    space = get_object_or_404(Space, pk=space_id)
    reviews = Review.objects.filter(space=space)
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    operation_description="Create a new review for a space",
    request_body=ReviewCreateSerializer,
    responses={201: ReviewSerializer(), 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, space_id):
    """Create a new review for a space"""
    space = get_object_or_404(Space, pk=space_id)
    
    # Check if the user has already reviewed this space
    existing_review = Review.objects.filter(user=request.user, space=space).first()
    if existing_review:
        return Response(
            {"detail": "You have already reviewed this space."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = ReviewCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(user=request.user, space=space)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a review
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        obj = super().get_object()
        # Check if the user is the creator of the review for update/delete
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj.user != self.request.user:
                self.permission_denied(
                    self.request, 
                    message="You do not have permission to modify this review."
                )
        return obj
