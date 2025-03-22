from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from .models import Pest, Disease, DetectionResult
from .serializers import (
    PestSerializer,
    DiseaseSerializer,
    DetectionResultSerializer,
    DetectionStatisticsSerializer
)
from .ai_models import get_plant_disease_classifier
import logging

logger = logging.getLogger(__name__)

class PestViewSet(viewsets.ModelViewSet):
    queryset = Pest.objects.all()
    serializer_class = PestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Pest.objects.all()
        crop_id = self.request.query_params.get('crop_id', None)
        if crop_id:
            queryset = queryset.filter(affected_crops__id=crop_id)
        return queryset

    @action(detail=True, methods=['get'])
    def affected_crops(self, request, pk=None):
        """Get all crops affected by this pest"""
        pest = self.get_object()
        from crops.serializers import CropSerializer
        serializer = CropSerializer(pest.affected_crops.all(), many=True)
        return Response(serializer.data)

class DiseaseViewSet(viewsets.ModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Disease.objects.all()
        crop_id = self.request.query_params.get('crop_id', None)
        if crop_id:
            queryset = queryset.filter(affected_crops__id=crop_id)
        return queryset

    @action(detail=True, methods=['get'])
    def affected_crops(self, request, pk=None):
        """Get all crops affected by this disease"""
        disease = self.get_object()
        from crops.serializers import CropSerializer
        serializer = CropSerializer(disease.affected_crops.all(), many=True)
        return Response(serializer.data)

class DetectionResultViewSet(viewsets.ModelViewSet):
    queryset = DetectionResult.objects.all()
    serializer_class = DetectionResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = DetectionResult.objects.all()
        crop_id = self.request.query_params.get('crop_id', None)
        farmer_id = self.request.query_params.get('farmer_id', None)
        
        if crop_id:
            queryset = queryset.filter(crop_id=crop_id)
        if farmer_id:
            queryset = queryset.filter(farmer_id=farmer_id)
        
        return queryset.order_by('-detection_date')

    @action(detail=False, methods=['post'])
    def detect(self, request):
        """Detect pests or diseases in an uploaded image"""
        if 'image_url' not in request.data or 'crop_id' not in request.data:
            return Response(
                {"error": "Both image_url and crop_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the classifier instance
            classifier = get_plant_disease_classifier()
            
            # Use the AI model to detect diseases
            detection_result = classifier.classify_image(request.data['image_url'])
            
            if not detection_result['success']:
                return Response(
                    {"error": detection_result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Find or create corresponding Disease/Pest records
            disease = None
            pest = None
            if detection_result['disease_detected']:
                disease_name = detection_result['classification']
                disease, _ = Disease.objects.get_or_create(
                    name=disease_name,
                    defaults={
                        'local_name': disease_name,
                        'description': f"AI-detected disease: {disease_name}",
                        'symptoms': "Automatically detected by AI model",
                        'prevention_methods': "Consult agricultural expert",
                        'treatment_methods': "Consult agricultural expert"
                    }
                )

            # Create detection result record
            detection_data = {
                'image_url': request.data['image_url'],
                'crop_id': request.data['crop_id'],
                'pest_id': pest.id if pest else None,
                'disease_id': disease.id if disease else None,
                'confidence_score': detection_result['confidence_score'],
                'recommendation': detection_result['recommendation']
            }

            serializer = DetectionResultSerializer(data=detection_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in disease detection: {str(e)}")
            return Response(
                {"error": "An error occurred during detection"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def provide_feedback(self, request, pk=None):
        """Provide feedback on a detection result"""
        result = self.get_object()
        is_correct = request.data.get('is_correct')
        feedback = request.data.get('feedback')

        if is_correct is None:
            return Response(
                {"error": "is_correct parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        result.is_correct = is_correct
        result.feedback = feedback
        result.save()

        return Response({"status": "feedback recorded"})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics about pest/disease detections"""
        crop_id = request.query_params.get('crop_id')
        
        queryset = DetectionResult.objects.all()
        if crop_id:
            queryset = queryset.filter(crop_id=crop_id)

        total_detections = queryset.count()
        correct_detections = queryset.filter(is_correct=True).count()
        accuracy = correct_detections / total_detections if total_detections > 0 else 0

        most_common_pests = Pest.objects.filter(
            detectionresult__isnull=False
        ).annotate(
            detection_count=Count('detectionresult')
        ).order_by('-detection_count')[:5]

        most_common_diseases = Disease.objects.filter(
            detectionresult__isnull=False
        ).annotate(
            detection_count=Count('detectionresult')
        ).order_by('-detection_count')[:5]

        detection_by_crop = DetectionResult.objects.values(
            'crop__name'
        ).annotate(
            count=Count('id')
        )

        data = {
            'total_detections': total_detections,
            'correct_detections': correct_detections,
            'accuracy': accuracy,
            'most_common_pests': most_common_pests,
            'most_common_diseases': most_common_diseases,
            'detection_by_crop': {
                item['crop__name']: item['count']
                for item in detection_by_crop
            }
        }

        serializer = DetectionStatisticsSerializer(data)
        return Response(serializer.data)
