from rest_framework import serializers
from .models import Space

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = [
            'id', 'name', 'location', 'capacity', 
            'image1', 'image2', 'image3', 'image4', 'image5',
            'status', 'description', 'equipment', 'features', 
            'price_per_hour', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be a positive integer.")
        return value

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Space name must be at least 2 characters long.")
        return value.strip()

    def to_representation(self, instance):
        """
        Override to_representation to add absolute URLs for image fields
        """
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Convert relative image URLs to absolute URLs
        for i in range(1, 6):
            image_field = f'image{i}'
            if data.get(image_field):
                if request:
                    data[image_field] = request.build_absolute_uri(data[image_field])
        
        return data