from django.contrib import admin
from .models import Crop, CropRecommendation, PlantingSchedule

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ['name', 'local_name', 'growing_season', 'soil_type']
    search_fields = ['name', 'local_name']
    list_filter = ['growing_season', 'soil_type']

@admin.register(CropRecommendation)
class CropRecommendationAdmin(admin.ModelAdmin):
    list_display = ['crop', 'soil_type', 'season', 'success_rate']
    search_fields = ['crop__name']
    list_filter = ['soil_type', 'season']

@admin.register(PlantingSchedule)
class PlantingScheduleAdmin(admin.ModelAdmin):
    list_display = ['crop', 'sowing_time', 'harvesting_time']
    search_fields = ['crop__name']
    list_filter = ['sowing_time']
