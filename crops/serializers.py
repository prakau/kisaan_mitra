from rest_framework import serializers
from .models import Crop, CropRecommendation, PlantingSchedule

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = '__all__'

class CropRecommendationSerializer(serializers.ModelSerializer):
    crop = CropSerializer(read_only=True)
    crop_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CropRecommendation
        fields = ['id', 'crop', 'crop_id', 'soil_type', 'season', 
                 'rainfall', 'temperature', 'success_rate', 'created_at']

class PlantingScheduleSerializer(serializers.ModelSerializer):
    crop = CropSerializer(read_only=True)
    crop_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = PlantingSchedule
        fields = ['id', 'crop', 'crop_id', 'sowing_time', 'harvesting_time',
                 'irrigation_schedule', 'fertilizer_schedule', 'created_at', 'updated_at']

class CropDetailSerializer(serializers.ModelSerializer):
    recommendations = CropRecommendationSerializer(many=True, read_only=True, source='croprecommendation_set')
    planting_schedules = PlantingScheduleSerializer(many=True, read_only=True, source='plantingschedule_set')
    
    class Meta:
        model = Crop
        fields = ['id', 'name', 'local_name', 'description', 'growing_season',
                 'water_requirement', 'soil_type', 'fertilizer_requirement',
                 'pest_susceptibility', 'harvesting_time', 'created_at',
                 'updated_at', 'recommendations', 'planting_schedules']
