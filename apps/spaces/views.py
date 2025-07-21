from django.shortcuts import render
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Space
from .serializers import SpaceSerializer

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

