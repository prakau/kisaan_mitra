from django.contrib import admin
from .models import Pest, Disease, DetectionResult

@admin.register(Pest)
class PestAdmin(admin.ModelAdmin):
    list_display = ['name', 'local_name', 'get_affected_crops']
    search_fields = ['name', 'local_name']
    filter_horizontal = ['affected_crops']

    def get_affected_crops(self, obj):
        return ", ".join([crop.name for crop in obj.affected_crops.all()])
    get_affected_crops.short_description = 'Affected Crops'

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'local_name', 'get_affected_crops']
    search_fields = ['name', 'local_name']
    filter_horizontal = ['affected_crops']

    def get_affected_crops(self, obj):
        return ", ".join([crop.name for crop in obj.affected_crops.all()])
    get_affected_crops.short_description = 'Affected Crops'

@admin.register(DetectionResult)
class DetectionResultAdmin(admin.ModelAdmin):
    list_display = ['crop', 'pest', 'disease', 'confidence_score',
                   'detection_date', 'is_correct']
    search_fields = ['crop__name', 'pest__name', 'disease__name']
    list_filter = ['crop', 'pest', 'disease', 'is_correct', 'detection_date']
    date_hierarchy = 'detection_date'
    readonly_fields = ['detection_date']
    raw_id_fields = ['crop', 'pest', 'disease']
