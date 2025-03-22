from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Crop, CropRecommendation, PlantingSchedule
from .serializers import (
    CropSerializer,
    CropDetailSerializer,
    CropRecommendationSerializer,
    PlantingScheduleSerializer
)

class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CropDetailSerializer
        return CropSerializer

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """Get recommendations for a specific crop"""
        crop = self.get_object()
        recommendations = CropRecommendation.objects.filter(crop=crop)
        serializer = CropRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def planting_schedules(self, request, pk=None):
        """Get planting schedules for a specific crop"""
        crop = self.get_object()
        schedules = PlantingSchedule.objects.filter(crop=crop)
        serializer = PlantingScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def recommend(self, request):
        """Get crop recommendations based on soil and weather conditions"""
        soil_type = request.data.get('soil_type')
        season = request.data.get('season')
        rainfall = request.data.get('rainfall')
        temperature = request.data.get('temperature')

        if not all([soil_type, season, rainfall, temperature]):
            return Response(
                {"error": "All parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get recommendations sorted by success rate
        recommendations = CropRecommendation.objects.filter(
            soil_type=soil_type,
            season=season,
            rainfall__lte=float(rainfall) + 100,
            rainfall__gte=float(rainfall) - 100,
            temperature__lte=float(temperature) + 5,
            temperature__gte=float(temperature) - 5
        ).order_by('-success_rate')

        serializer = CropRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)

class CropRecommendationViewSet(viewsets.ModelViewSet):
    queryset = CropRecommendation.objects.all()
    serializer_class = CropRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CropRecommendation.objects.all()
        crop_id = self.request.query_params.get('crop_id', None)
        if crop_id is not None:
            queryset = queryset.filter(crop_id=crop_id)
        return queryset

class PlantingScheduleViewSet(viewsets.ModelViewSet):
    queryset = PlantingSchedule.objects.all()
    serializer_class = PlantingScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PlantingSchedule.objects.all()
        crop_id = self.request.query_params.get('crop_id', None)
        if crop_id is not None:
            queryset = queryset.filter(crop_id=crop_id)
        return queryset
