from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    list_spaces, space_detail, space_images, 
    ReviewViewSet, space_reviews, create_review, 
    ReviewDetailView
)

# Create a router for ReviewViewSet
router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    # Space URLs
    path('', list_spaces, name='list-spaces'),
    path('<int:pk>/', space_detail, name='space-detail'),
    path('<int:pk>/images/', space_images, name='space-images'),
    
    # Review URLs
    path('', include(router.urls)),
    path('<int:space_id>/reviews/', space_reviews, name='space-reviews'),
    path('<int:space_id>/reviews/create/', create_review, name='create-review'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
]