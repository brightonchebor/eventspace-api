from django.db import models

# Create your models here.
class Space(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('free', 'Free'),
    ]
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    capacity = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='free'
    )
    # Replace single image field with five separate image fields
    image1 = models.ImageField(upload_to='spaces/images/', blank=True, null=True)
    image2 = models.ImageField(upload_to='spaces/images/', blank=True, null=True)
    image3 = models.ImageField(upload_to='spaces/images/', blank=True, null=True)
    image4 = models.ImageField(upload_to='spaces/images/', blank=True, null=True)
    image5 = models.ImageField(upload_to='spaces/images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    equipment = models.TextField(blank=True, null=True)
    features = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

