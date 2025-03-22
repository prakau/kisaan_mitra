from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    pass

class FarmerProfile(models.Model):
    LANGUAGE_CHOICES = [
        ('hi', 'Hindi'),
        ('hr', 'Haryanvi'),
        ('en', 'English')
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    district = models.CharField(max_length=100)
    village = models.CharField(max_length=100, default='')
    preferred_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default='hi'
    )

class FarmLot(models.Model):
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='farm_lots')
    area = models.DecimalField(max_digits=10, decimal_places=2)  # in acres
    soil_type = models.CharField(max_length=100)
    location = models.CharField(max_length=255)  # Can be enhanced with GeoDjango later
    current_crop = models.CharField(max_length=100, blank=True, null=True)

class Query(models.Model):
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='queries')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolution = models.TextField(blank=True, null=True)
