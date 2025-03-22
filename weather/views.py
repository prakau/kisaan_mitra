from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q, F, Min, Max
from django.db.models.functions import Extract
from django.contrib.postgres.aggregates import ArrayAgg
from datetime import timedelta
from decimal import Decimal

from .models import Location, WeatherData, WeatherForecast, WeatherAlert
from .serializers import (
    LocationSerializer,
    WeatherDataSerializer,
    WeatherForecastSerializer,
    WeatherAlertSerializer,
    LocationWeatherSerializer,
    WeatherStatsSerializer,
    HistoricalWeatherSerializer
)
from .language_utils import WeatherTranslator
from .repositories import WeatherRepository
from .config import WEATHER_CONFIG
from .exceptions import InvalidLocationError, WeatherDataError

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """List all locations with language support."""
        language = request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])
        serializer = LocationSerializer(self.queryset, many=True, context={'language': language})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Retrieve a specific location with language support."""
        language = request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])
        try:
            location = Location.objects.get(pk=pk)
        except Location.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = LocationSerializer(location, context={'language': language})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find locations within a specified radius with language support."""
        lat = request.query_params.get('latitude')
        lon = request.query_params.get('longitude')
        radius = request.query_params.get('radius', 10)  # Default 10km radius
        language = request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])

        if not all([lat, lon]):
            return Response(
                {"error": "latitude and longitude parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat = Decimal(lat)
            lon = Decimal(lon)
            radius = float(radius)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid coordinate or radius values"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Using the Haversine formula for distance calculation
        locations = Location.objects.raw("""
            SELECT *,
            (6371 * acos(cos(radians(%s)) * cos(radians(latitude))
            * cos(radians(longitude) - radians(%s)) + sin(radians(%s))
            * sin(radians(latitude)))) AS distance
            FROM weather_location
            HAVING distance < %s
            ORDER BY distance
        """, [lat, lon, lat, radius])

        serializer = LocationSerializer(locations, many=True, context={'language': language})
        return Response(serializer.data)

class WeatherDataViewSet(viewsets.ModelViewSet):
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = WeatherData.objects.all().select_related('location')
        location_id = self.request.query_params.get('location_id')
        district = self.request.query_params.get('district')
        
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        elif district:
            queryset = queryset.filter(location__district=district)
            
        return queryset.order_by('-timestamp')

    @action(detail=False, methods=['get'])
    def agricultural_metrics(self, request):
        """Get weather metrics specifically relevant for agriculture with language support."""
        location_id = request.query_params.get('location_id')
        language = request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])
        
        if not location_id:
            return Response(
                {"error": "location_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            weather = WeatherData.objects.get(location_id=location_id)
        except WeatherData.DoesNotExist:
            return Response(
                {"error": "No weather data available for this location"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WeatherDataSerializer(weather, context={'language': language})
        return Response(serializer.data)

class WeatherForecastViewSet(viewsets.ModelViewSet):
    queryset = WeatherForecast.objects.all()
    serializer_class = WeatherForecastSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = WeatherForecast.objects.all().select_related('location')
        location_id = self.request.query_params.get('location_id')
        district = self.request.query_params.get('district')
        
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        elif district:
            queryset = queryset.filter(location__district=district)
            
        return queryset.order_by('forecast_date')

    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get 7-day weather forecast with agricultural insights and language support."""
        location_id = request.query_params.get('location_id')
        language = request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])
        
        if not location_id:
            return Response(
                {"error": "location_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        forecasts = WeatherForecast.objects.filter(location_id=location_id)
        serializer = WeatherForecastSerializer(forecasts, many=True, context={'language': language})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def monthly_outlook(self, request):
        """Get monthly weather outlook for agricultural planning with language support"""
        location_id = request.query_params.get('location_id')
        language = request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])
        
        if not location_id:
            return Response(
                {"error": "location_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = timezone.now().date()
        forecasts = WeatherForecast.objects.filter(
            location_id=location_id,
            forecast_date__gte=today,
            forecast_date__lt=today + timedelta(days=30)
        ).order_by('forecast_date')

        # Weekly aggregations with translated labels
        translator = WeatherTranslator(language)
        weekly_stats = []
        for i in range(4):  # 4 weeks
            week_start = today + timedelta(days=i*7)
            week_end = week_start + timedelta(days=7)
            week_forecasts = [f for f in forecasts if week_start <= f.forecast_date < week_end]
            
            if week_forecasts:
                weekly_stats.append({
                    'week_starting': week_start,
                    'avg_temperature': sum((f.max_temperature + f.min_temperature)/2 for f in week_forecasts) / len(week_forecasts),
                    'total_expected_rainfall': sum(f.expected_rainfall for f in week_forecasts),
                    'frost_risk_days': translator.get_farming_action('FROST_RISK_DAYS', count=sum(1 for f in week_forecasts if f.frost_risk)),
                    'heat_stress_days': translator.get_farming_action('HEAT_STRESS_DAYS', count=sum(1 for f in week_forecasts if f.heat_stress_risk)),
                    'favorable_days': translator.get_farming_action('FAVORABLE_DAYS', count=sum(1 for f in week_forecasts if 15 <= (f.max_temperature + f.min_temperature)/2 <= 30))
                })

        return Response({
            'weekly_outlook': weekly_stats,
            'monthly_summary': {
                'total_expected_rainfall': sum(week['total_expected_rainfall'] for week in weekly_stats),
                'avg_favorable_days_per_week': translator.get_farming_action('AVG_FAVORABLE_DAYS', days=sum(week['favorable_days']['count'] for week in weekly_stats) / len(weekly_stats)),
                'extreme_weather_risk': translator.get_alert_type('EXTREME_WEATHER_RISK') if any(
                    week['frost_risk_days']['count'] > 2 or week['heat_stress_days']['count'] > 2
                    for week in weekly_stats
                ) else translator.get_alert_type('MODERATE_WEATHER_RISK')
            }
        })

class WeatherAlertViewSet(viewsets.ModelViewSet):
    queryset = WeatherAlert.objects.all()
    serializer_class = WeatherAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = WeatherAlert.objects.all().select_related('location')
        location_id = self.request.query_params.get('location_id')
        district = self.request.query_params.get('district')
        crop_id = self.request.query_params.get('crop_id')
        alert_type = self.request.query_params.get('alert_type')
        severity = self.request.query_params.get('severity')
        language = self.request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])
        
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        elif district:
            queryset = queryset.filter(location__district=district)
            
        if crop_id:
            queryset = queryset.filter(affected_crops__id=crop_id)
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        if severity:
            queryset = queryset.filter(severity=severity)
            
        return queryset.filter(is_active=True).order_by('-severity', '-start_time')

    def list(self, request):
        """List alerts with language support"""
        language = request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])
        queryset = self.get_queryset()
        serializer = WeatherAlertSerializer(queryset, many=True, context={'language': language})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active weather alerts with agricultural impact assessment"""
        location_id = request.query_params.get('location_id')
        crop_id = request.query_params.get('crop_id')
        language = request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])
        
        if not location_id:
            return Response(
                {"error": "location_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        base_query = Q(
            location_id=location_id,
            is_active=True,
            end_time__gt=timezone.now()
        )

        if crop_id:
            base_query &= Q(affected_crops__id=crop_id)

        alerts = (WeatherAlert.objects.filter(base_query)
                 .select_related('location')
                 .prefetch_related('affected_crops')
                 .order_by('-severity', '-start_time'))

        serializer = WeatherAlertSerializer(alerts, many=True, context={'language': language})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark a weather alert as resolved with resolution details"""
        alert = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        actual_impact = request.data.get('actual_impact', '')
        
        alert.is_active = False
        alert.resolution_notes = resolution_notes
        alert.actual_impact = actual_impact
        alert.resolved_at = timezone.now()
        alert.save()
        
        return Response({
            "status": "alert resolved",
            "resolution_time": alert.resolved_at,
            "total_duration_hours": (alert.resolved_at - alert.start_time).total_seconds() / 3600
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get alert statistics for analysis"""
        location_id = request.query_params.get('location_id')
        days = int(request.query_params.get('days', 30))
        crop_id = request.query_params.get('crop_id')
        
        if not location_id:
            return Response(
                {"error": "location_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_date = timezone.now() - timedelta(days=days)
        base_query = Q(
            location_id=location_id,
            start_time__gte=start_date
        )
        
        if crop_id:
            base_query &= Q(affected_crops__id=crop_id)
        
        alerts = WeatherAlert.objects.filter(base_query)

        stats = {
            'total_alerts': alerts.count(),
            'by_severity': alerts.values('severity').annotate(count=Count('id')),
            'by_type': alerts.values('alert_type').annotate(count=Count('id')),
            'most_affected_crops': (
                alerts.values('affected_crops__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            ),
            'average_duration_hours': alerts.filter(
                resolved_at__isnull=False
            ).aggregate(
                avg_duration=Avg(F('resolved_at') - F('start_time'))
            )['avg_duration']
        }

        return Response(stats)

class LocationWeatherViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get comprehensive weather information with localized agricultural insights"""
        location_id = request.query_params.get('location_id')
        crop_id = request.query_params.get('crop_id')
        language = request.query_params.get('language', WEATHER_CONFIG['DEFAULT_LANGUAGE'])
        
        if not location_id:
            return Response(
                {"error": "location_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            location = Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            return Response(
                {"error": "Location not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get current weather with agricultural metrics
        current_weather = (WeatherData.objects.filter(location_id=location_id)
                         .select_related('location')
                         .order_by('-timestamp')
                         .first())
        
        if not current_weather:
            return Response(
                {"error": "No weather data available for this location"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get active alerts
        active_alerts = (WeatherAlert.objects.filter(
            location_id=location_id,
            is_active=True,
            end_time__gt=timezone.now()
        ).select_related('location')
         .prefetch_related('affected_crops')
         .order_by('-severity'))

        # Get forecasts with agricultural insights
        today = timezone.now().date()
        forecasts = (WeatherForecast.objects.filter(
            location_id=location_id,
            forecast_date__gte=today,
            forecast_date__lt=today + timedelta(days=7)
        ).select_related('location')
         .order_by('forecast_date'))

        # Get historical context and soil conditions
        last_week = timezone.now() - timedelta(days=7)
        historical_stats = WeatherData.objects.filter(
            location_id=location_id,
            timestamp__gte=last_week
        ).aggregate(
            avg_temp=Avg('temperature'),
            min_temp=Min('temperature'),
            max_temp=Max('temperature'),
            avg_humidity=Avg('humidity'),
            total_rainfall=Sum('rainfall'),
            avg_soil_moisture=Avg('soil_moisture'),
            avg_soil_temp=Avg('soil_temperature')
        )

        data = {
            'location': {
                'id': location.id,
                'name': location.name,
                'district': location.district,
                'state': location.state,
                'coordinates': {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'elevation': location.elevation
                }
            },
            'current_weather': WeatherDataSerializer(current_weather).data,
            'historical_context': historical_stats,
            'active_alerts': WeatherAlertSerializer(active_alerts, many=True).data,
            'forecasts': [],
            'agricultural_summary': {
                'current_conditions': {
                    'frost_risk': current_weather.temperature <= 2,
                    'heat_stress_risk': current_weather.temperature >= 35,
                    'disease_risk': (
                        current_weather.humidity >= 80 and 
                        current_weather.temperature >= 20
                    ),
                    'ideal_conditions': (
                        15 <= current_weather.temperature <= 30 and
                        40 <= current_weather.humidity <= 70
                    ),
                    'soil_health': {
                        'moisture_status': (
                            'dry' if current_weather.soil_moisture < 30 else
                            'saturated' if current_weather.soil_moisture > 70 else
                            'optimal'
                        ),
                        'temperature_status': (
                            'cold' if current_weather.soil_temperature < 10 else
                            'hot' if current_weather.soil_temperature > 35 else
                            'optimal'
                        )
                    },
                    'irrigation_needed': (
                        current_weather.soil_moisture and 
                        current_weather.soil_moisture < 30
                    )
                },
                'alert_summary': {
                    'total_active': active_alerts.count(),
                    'high_severity': active_alerts.filter(severity__in=['HIGH', 'EXTREME']).count(),
                    'types': active_alerts.values('alert_type').annotate(count=Count('id'))
                },
                'weekly_outlook': {
                    'total_expected_rainfall': sum(f.expected_rainfall for f in forecasts),
                    'frost_risk_days': sum(1 for f in forecasts if f.frost_risk),
                    'heat_stress_days': sum(1 for f in forecasts if f.heat_stress_risk),
                    'favorable_days': sum(1 for f in forecasts if 15 <= (f.max_temperature + f.min_temperature)/2 <= 30)
                }
            }
        }

        # Process forecasts with agricultural insights
        for forecast in forecasts:
            forecast_data = WeatherForecastSerializer(forecast).data
            
            # Add agricultural risk assessments
            forecast_data['agricultural_risks'] = {
                'frost_risk': forecast.min_temperature <= 2,
                'heat_stress_risk': forecast.max_temperature >= 35,
                'disease_risk': (
                    forecast.humidity >= 80 and 
                    ((forecast.max_temperature + forecast.min_temperature) / 2) >= 20
                ),
                'ideal_growing_conditions': (
                    15 <= forecast.max_temperature <= 30 and
                    40 <= forecast.humidity <= 70 and
                    forecast.expected_rainfall > 0
                )
            }
            
            # Add crop-specific insights if crop_id is provided
            if crop_id:
                from crops.models import Crop
                try:
                    crop = Crop.objects.get(id=crop_id)
                    forecast_data['crop_specific'] = {
                        'crop_name': crop.name,
                        'temperature_suitable': (
                            crop.min_temp <= forecast.max_temperature <= crop.max_temp
                        ),
                        'humidity_suitable': (
                            crop.min_humidity <= forecast.humidity <= crop.max_humidity
                        ),
                        'water_requirement': (
                            'high' if forecast.rainfall_probability < 30 else
                            'low' if forecast.rainfall_probability > 70 else
                            'moderate'
                        ),
                        'recommended_actions': []
                    }
                    
                    # Add recommended actions based on conditions
                    if forecast.min_temperature <= crop.min_temp:
                        forecast_data['crop_specific']['recommended_actions'].append(
                            "Protect crop from cold conditions"
                        )
                    if forecast.max_temperature >= crop.max_temp:
                        forecast_data['crop_specific']['recommended_actions'].append(
                            "Implement heat stress mitigation measures"
                        )
                    if forecast.humidity > crop.max_humidity:
                        forecast_data['crop_specific']['recommended_actions'].append(
                            "Monitor for disease due to high humidity"
                        )
                    if forecast.rainfall_probability < 30:
                        forecast_data['crop_specific']['recommended_actions'].append(
                            "Plan for irrigation"
                        )
                except Crop.DoesNotExist:
                    pass
            
            data['forecasts'].append(forecast_data)

        return Response(data)
