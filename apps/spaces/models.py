from django.db import models

# Create your models here.
class Space(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    capacity = models.IntegerField()
    image = models.ImageField(upload_to='spaces/', blank=True, null=True)
    status = models.CharField(
        max_length=20,  )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    equipment = models.TextField(blank=True, null=True)
    features = models.TextField(blank=True, null=True)
    

    def __str__(self):
        return self.name