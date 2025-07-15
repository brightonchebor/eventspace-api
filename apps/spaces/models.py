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
    image1 = models.JSONField(default=list, blank=True)
    image2 = models.JSONField(default=list, blank=True)
    image3 = models.JSONField(default=list, blank=True)
    image4 = models.JSONField(default=list, blank=True)
    image5 = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    equipment = models.TextField(blank=True, null=True)
    features = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

