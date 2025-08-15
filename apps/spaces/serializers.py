from rest_framework import serializers
from .models import Space, Review

class SpaceSerializer(serializers.ModelSerializer):
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Space
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'review_count', 'average_rating']
        
    def get_review_count(self, obj):
        return obj.reviews.count()
        
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be a positive integer.")
        return value

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Space name must be at least 2 characters long.")
        return value.strip()


class ReviewSerializer(serializers.ModelSerializer):
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    space_name = serializers.CharField(source='space.name', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'space', 'user', 'rating', 'comment', 'created_at', 'updated_at', 'user_first_name', 'space_name']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_first_name', 'space_name']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
        
    def validate_comment(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Comment must be at least 5 characters long.")
        return value.strip()


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['space', 'rating', 'comment']
        
    def create(self, validated_data):
        # Current user becomes the reviewer
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
