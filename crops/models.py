from django.db import models

class Crop(models.Model):
    name = models.CharField(max_length=100)
    local_name = models.CharField(max_length=100)  # Name in Hindi/Haryanvi
    description = models.TextField()
    growing_season = models.CharField(max_length=50)
    water_requirement = models.TextField()
    soil_type = models.CharField(max_length=100)
    fertilizer_requirement = models.TextField()
    pest_susceptibility = models.TextField()
    harvesting_time = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class CropRecommendation(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    soil_type = models.CharField(max_length=100)
    season = models.CharField(max_length=50)
    rainfall = models.FloatField()
    temperature = models.FloatField()
    success_rate = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.crop.name}"

class PlantingSchedule(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    sowing_time = models.CharField(max_length=100)
    harvesting_time = models.CharField(max_length=100)
    irrigation_schedule = models.TextField()
    fertilizer_schedule = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Schedule for {self.crop.name}"
