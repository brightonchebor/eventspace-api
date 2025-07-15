from django.test import TestCase
<<<<<<< HEAD

# Create your tests here.
=======
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Space

class SpaceViewTestCase(APITestCase):
    
    def setUp(self):
        """Set up test data"""
        self.create_url = reverse('create-space')
        self.list_url = reverse('list-spaces')
        
        # Create a test space
        self.test_space = Space.objects.create(
            name="Test Conference Room",
            location="Building A, Floor 1",
            capacity=50,
            status="available",
            description="A modern conference room with projector",
            equipment="Projector, Whiteboard, Conference table",
            features="Air conditioning, WiFi, Natural lighting"
        )

    def test_create_space_success(self):
        """Test successful space creation"""
        data = {
            'name': 'Meeting Room B',
            'location': 'Building B, Floor 2',
            'capacity': 25,
            'status': 'available',
            'description': 'Small meeting room for team discussions',
            'equipment': 'TV screen, Chairs',
            'features': 'WiFi, Air conditioning'
        }
        
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('Meeting Room B', response.data['message'])
        self.assertEqual(Space.objects.count(), 2)

    def test_create_space_invalid_data(self):
        """Test space creation with invalid data"""
        data = {
            'name': '',  # Empty name should fail validation
            'location': 'Test Location',
            'capacity': -5,  # Negative capacity should fail
        }
        
        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)

    def test_list_spaces(self):
        """Test listing all spaces"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Conference Room')
>>>>>>> origin/playground
