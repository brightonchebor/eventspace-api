from rest_framework import serializers
from .models import Space

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be a positive integer.")
        return value

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Space name must be at least 2 characters long.")
        return value.strip()
    
# Serializer for deleting a space (can be empty, as only the ID is needed)
class SpaceDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
