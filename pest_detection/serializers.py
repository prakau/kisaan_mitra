from rest_framework import serializers
from .models import Pest, Disease, DetectionResult
from crops.serializers import CropSerializer

class PestSerializer(serializers.ModelSerializer):
    affected_crops = CropSerializer(many=True, read_only=True)
    affected_crop_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Pest
        fields = ['id', 'name', 'local_name', 'description', 'affected_crops',
                 'affected_crop_ids', 'symptoms', 'prevention_methods',
                 'treatment_methods', 'image_url', 'created_at', 'updated_at']

    def create(self, validated_data):
        affected_crop_ids = validated_data.pop('affected_crop_ids', [])
        pest = Pest.objects.create(**validated_data)
        pest.affected_crops.set(affected_crop_ids)
        return pest

class DiseaseSerializer(serializers.ModelSerializer):
    affected_crops = CropSerializer(many=True, read_only=True)
    affected_crop_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Disease
        fields = ['id', 'name', 'local_name', 'description', 'affected_crops',
                 'affected_crop_ids', 'symptoms', 'prevention_methods',
                 'treatment_methods', 'image_url', 'created_at', 'updated_at']

    def create(self, validated_data):
        affected_crop_ids = validated_data.pop('affected_crop_ids', [])
        disease = Disease.objects.create(**validated_data)
        disease.affected_crops.set(affected_crop_ids)
        return disease

class DetectionResultSerializer(serializers.ModelSerializer):
    crop = CropSerializer(read_only=True)
    crop_id = serializers.IntegerField(write_only=True)
    pest = PestSerializer(read_only=True)
    pest_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    disease = DiseaseSerializer(read_only=True)
    disease_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = DetectionResult
        fields = ['id', 'image_url', 'crop', 'crop_id', 'pest', 'pest_id',
                 'disease', 'disease_id', 'confidence_score', 'detection_date',
                 'recommendation', 'feedback', 'is_correct']

    def validate(self, data):
        """
        Check that at least one of pest_id or disease_id is provided
        """
        if not data.get('pest_id') and not data.get('disease_id'):
            raise serializers.ValidationError(
                "Either pest_id or disease_id must be provided"
            )
        return data

class DetectionStatisticsSerializer(serializers.Serializer):
    total_detections = serializers.IntegerField()
    correct_detections = serializers.IntegerField()
    accuracy = serializers.FloatField()
    most_common_pests = PestSerializer(many=True)
    most_common_diseases = DiseaseSerializer(many=True)
    detection_by_crop = serializers.DictField(
        child=serializers.IntegerField()
    )
