from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
    
    def test_password_reset_flow(self):
        # Test reset request
        response = self.client.post('/api/auth/password-reset/', {'email': 'test@example.com'})
        self.assertEqual(response.status_code, 200)
        
        