from django.db import models

class Pest(models.Model):
    name = models.CharField(max_length=100)
    local_name = models.CharField(max_length=100)  # Name in Hindi/Haryanvi
    description = models.TextField()
    affected_crops = models.ManyToManyField('crops.Crop', related_name='susceptible_pests')
    symptoms = models.TextField()
    prevention_methods = models.TextField()
    treatment_methods = models.TextField()
    image_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100)
    local_name = models.CharField(max_length=100)  # Name in Hindi/Haryanvi
    description = models.TextField()
    affected_crops = models.ManyToManyField('crops.Crop', related_name='susceptible_diseases')
    symptoms = models.TextField()
    prevention_methods = models.TextField()
    treatment_methods = models.TextField()
    image_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class DetectionResult(models.Model):
    image_url = models.URLField()
    crop = models.ForeignKey('crops.Crop', on_delete=models.CASCADE)
    pest = models.ForeignKey(Pest, null=True, blank=True, on_delete=models.SET_NULL)
    disease = models.ForeignKey(Disease, null=True, blank=True, on_delete=models.SET_NULL)
    confidence_score = models.FloatField()
    detection_date = models.DateTimeField(auto_now_add=True)
    recommendation = models.TextField()
    feedback = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField(null=True)

    def __str__(self):
        return f"Detection for {self.crop.name} on {self.detection_date}"
