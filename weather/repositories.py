"""
Repository pattern implementation for weather data access.
Centralizes data access operations and adds a layer of abstraction.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from django.utils import timezone
from django.db.models import QuerySet, Avg, Sum, Min, Max, Count, F, Q
from django.core.cache import cache

from .models import Location, WeatherData, WeatherForecast, WeatherAlert
from .exceptions import InvalidLocationError, WeatherDataError
from .config import WEATHER_CONFIG, TIME_INTERVALS

class WeatherRepository:
    """
    Repository for weather-related database operations.
    Implements caching and optimized queries.
    """

    def get_location(self, location_id: int) -> Optional[Location]:
        """Get a location by ID with caching."""
        cache_key = f"{WEATHER_CONFIG['CACHE_KEY_PREFIX']}location_{location_id}"
        location = cache.get(cache_key)
        
        if not location:
            try:
                location = Location.objects.get(id=location_id)
                cache.set(cache_key, location, WEATHER_CONFIG['CACHE_TIMEOUT'])
            except Location.DoesNotExist:
                raise InvalidLocationError(f"Location with id {location_id} not found")
        
        return location

    def get_current_weather(self, location_id: int) -> Optional[WeatherData]:
        """Get the most recent weather data for a location."""
        cache_key = f"{WEATHER_CONFIG['CACHE_KEY_PREFIX']}current_weather_{location_id}"
        weather_data = cache.get(cache_key)
        
        if not weather_data:
            cutoff_time = timezone.now() - timedelta(
                hours=TIME_INTERVALS['CURRENT_WEATHER']
            )
            weather_data = (
                WeatherData.objects
                .filter(location_id=location_id, timestamp__gte=cutoff_time)
                .select_related('location')
                .order_by('-timestamp')
                .first()
            )
            if weather_data:
                cache.set(cache_key, weather_data, WEATHER_CONFIG['CACHE_TIMEOUT'])
                
        return weather_data

    def get_weather_history(
        self, 
        location_id: int, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get historical weather data with aggregated statistics."""
        start_date = timezone.now() - timedelta(days=days)
        
        return (
            WeatherData.objects
            .filter(location_id=location_id, timestamp__gte=start_date)
            .annotate(date=F('timestamp__date'))
            .values('date')
            .annotate(
                avg_temp=Avg('temperature'),
                min_temp=Min('temperature'),
                max_temp=Max('temperature'),
                total_rainfall=Sum('rainfall'),
                avg_humidity=Avg('humidity'),
                avg_soil_moisture=Avg('soil_moisture'),
                avg_soil_temp=Avg('soil_temperature')
            )
            .order_by('date')
        )

    def get_active_alerts(
        self, 
        location_id: int, 
        crop_id: Optional[int] = None
    ) -> QuerySet:
        """Get active weather alerts for a location."""
        query = Q(
            location_id=location_id,
            is_active=True,
            end_time__gt=timezone.now()
        )
        
        if crop_id:
            query &= Q(affected_crops__id=crop_id)
            
        return (
            WeatherAlert.objects
            .filter(query)
            .select_related('location')
            .prefetch_related('affected_crops')
            .order_by('-severity', '-start_time')
        )

    def get_weather_forecast(
        self, 
        location_id: int, 
        days: int = 7
    ) -> QuerySet:
        """Get weather forecast for specified number of days."""
        if days > WEATHER_CONFIG['MAX_FORECAST_DAYS']:
            days = WEATHER_CONFIG['MAX_FORECAST_DAYS']
            
        today = timezone.now().date()
        return (
            WeatherForecast.objects
            .filter(
                location_id=location_id,
                forecast_date__gte=today,
                forecast_date__lt=today + timedelta(days=days)
            )
            .select_related('location')
            .order_by('forecast_date')
        )

    def get_nearby_locations(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = WEATHER_CONFIG['DEFAULT_RADIUS_KM']
    ) -> QuerySet:
        """Get locations within specified radius using Haversine formula."""
        return Location.objects.raw("""
            SELECT *, 
            (6371 * acos(cos(radians(%s)) * cos(radians(latitude))
            * cos(radians(longitude) - radians(%s)) + sin(radians(%s))
            * sin(radians(latitude)))) AS distance
            FROM weather_location
            HAVING distance < %s
            ORDER BY distance
        """, [latitude, longitude, latitude, radius_km])

    def create_weather_data(self, data: Dict[str, Any]) -> WeatherData:
        """Create new weather data with validation."""
        self._validate_weather_data(data)
        return WeatherData.objects.create(**data)

    def create_weather_alert(
        self, 
        data: Dict[str, Any], 
        affected_crop_ids: List[int]
    ) -> WeatherAlert:
        """Create new weather alert with affected crops."""
        alert = WeatherAlert.objects.create(**data)
        if affected_crop_ids:
            alert.affected_crops.set(affected_crop_ids)
        return alert

    def _validate_weather_data(self, data: Dict[str, Any]) -> None:
        """Validate weather data against configured thresholds."""
        validation = WEATHER_CONFIG['VALIDATION']
        
        if not validation['MIN_TEMPERATURE'] <= data.get('temperature', 0) <= validation['MAX_TEMPERATURE']:
            raise WeatherDataError("Temperature out of valid range")
            
        if not validation['MIN_HUMIDITY'] <= data.get('humidity', 0) <= validation['MAX_HUMIDITY']:
            raise WeatherDataError("Humidity out of valid range")
            
        if data.get('wind_speed', 0) > validation['MAX_WIND_SPEED']:
            raise WeatherDataError("Wind speed out of valid range")
            
        if data.get('rainfall', 0) > validation['MAX_RAINFALL']:
            raise WeatherDataError("Rainfall out of valid range")