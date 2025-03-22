"""
Models for the weather application.
Defines database schema for weather-related data with validation and utility methods.
"""

from typing import Optional, List
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

from .config import WEATHER_CONFIG, ALERT_SEVERITY_LEVELS, WEATHER_CONDITIONS
from .exceptions import WeatherDataValidationError

class Location(models.Model):
    """
    Represents a geographical location for weather monitoring.
    
    Attributes:
        name (str): Name of the location (village/city)
        district (str): District name
        state (str): State name (defaults to Haryana)
        latitude (Decimal): Geographical latitude
        longitude (Decimal): Geographical longitude
        elevation (float): Elevation above sea level in meters
    """
    name: str = models.CharField(
        max_length=100,
        help_text="Name of the location (village/city)"
    )
    district: str = models.CharField(
        max_length=100,
        help_text="District name"
    )
    state: str = models.CharField(
        max_length=100,
        default='Haryana',
        help_text="State name (defaults to Haryana)"
    )
    latitude: Decimal = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text="Geographical latitude (-90 to 90)"
    )
    longitude: Decimal = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text="Geographical longitude (-180 to 180)"
    )
    elevation: Optional[float] = models.FloatField(
        help_text="Elevation in meters",
        null=True,
        blank=True
    )
    
    class Meta:
        unique_together = ['latitude', 'longitude']
        indexes = [
            models.Index(fields=['district']),
            models.Index(fields=['state']),
            models.Index(fields=['latitude', 'longitude'])
        ]
        
    def __str__(self) -> str:
        return f"{self.name}, {self.district}"

    def clean(self) -> None:
        """Validate location data."""
        super().clean()
        if self.elevation is not None and self.elevation < 0:
            raise ValidationError({
                'elevation': 'Elevation cannot be negative'
            })

    def get_distance_to(self, lat: Decimal, lon: Decimal) -> float:
        """Calculate distance to another point using Haversine formula."""
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            R = 6371  # Earth radius in kilometers
            dlat = radians(float(lat2 - lat1))
            dlon = radians(float(lon2 - lon1))
            lat1 = radians(float(lat1))
            lat2 = radians(float(lat2))
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c
            
        return haversine(self.latitude, self.longitude, lat, lon)

    def get_current_weather(self) -> Optional['WeatherData']:
        """Get the most recent weather data for this location."""
        cutoff_time = timezone.now() - timezone.timedelta(
            hours=WEATHER_CONFIG['CACHE_TIMEOUT']
        )
        return (
            self.weatherdata_set
            .filter(timestamp__gte=cutoff_time)
            .order_by('-timestamp')
            .first()
        )

    def get_active_alerts(self) -> models.QuerySet['WeatherAlert']:
        """Get all active weather alerts for this location."""
        return (
            self.weatheralert_set
            .filter(
                is_active=True,
                end_time__gt=timezone.now()
            )
            .order_by('-severity', '-start_time')
        )

class WeatherData(models.Model):
    """
    Records weather measurements for a specific location and time.
    
    Attributes:
        location (Location): The location where weather was measured
        temperature (float): Temperature in Celsius
        humidity (float): Relative humidity percentage
        rainfall (float): Rainfall in millimeters
        wind_speed (float): Wind speed in km/h
        wind_direction (int): Wind direction in degrees
        soil_temperature (float): Soil temperature in Celsius
        soil_moisture (float): Soil moisture percentage
        solar_radiation (float): Solar radiation in W/m²
        weather_condition (str): General weather condition
        timestamp (datetime): When the measurement was taken
        data_source (str): Source of the weather data
    """
    
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        help_text="Location where weather was measured"
    )
    temperature = models.FloatField(
        validators=[
            MinValueValidator(WEATHER_CONFIG['VALIDATION']['MIN_TEMPERATURE']),
            MaxValueValidator(WEATHER_CONFIG['VALIDATION']['MAX_TEMPERATURE'])
        ]
    )
    humidity = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Relative humidity percentage"
    )
    rainfall = models.FloatField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(WEATHER_CONFIG['VALIDATION']['MAX_RAINFALL'])
        ],
        help_text="Rainfall in mm"
    )
    wind_speed = models.FloatField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(WEATHER_CONFIG['VALIDATION']['MAX_WIND_SPEED'])
        ],
        help_text="Wind speed in km/h"
    )
    wind_direction = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(360)],
        help_text="Wind direction in degrees"
    )
    soil_temperature = models.FloatField(
        null=True,
        blank=True,
        help_text="Soil temperature in Celsius"
    )
    soil_moisture = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Soil moisture percentage"
    )
    solar_radiation = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Solar radiation in W/m²"
    )
    weather_condition = models.CharField(
        max_length=100,
        choices=[(k, v) for k, v in WEATHER_CONDITIONS.items()]
    )
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    data_source = models.CharField(
        max_length=50,
        help_text="Source of weather data (e.g., IMD, Local Station)"
    )

    class Meta:
        indexes = [
            models.Index(fields=['location', '-timestamp']),
            models.Index(fields=['-timestamp']),
            models.Index(fields=['location', 'weather_condition']),
            models.Index(fields=['temperature', 'humidity']),
        ]
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f"Weather at {self.location} on {self.timestamp}"

    def clean(self) -> None:
        """Validate weather data."""
        super().clean()
        if self.timestamp > timezone.now():
            raise ValidationError({
                'timestamp': 'Timestamp cannot be in the future'
            })
        
        self._validate_soil_data()
        
    def _validate_soil_data(self) -> None:
        """Validate soil-related measurements."""
        if self.soil_temperature is not None:
            if not (WEATHER_CONFIG['VALIDATION']['MIN_TEMPERATURE'] <=
                   self.soil_temperature <=
                   WEATHER_CONFIG['VALIDATION']['MAX_TEMPERATURE']):
                raise ValidationError({
                    'soil_temperature': 'Soil temperature out of valid range'
                })

    def get_agricultural_metrics(self) -> dict:
        """Calculate agricultural metrics from weather data."""
        return {
            'growing_degree_days': self._calculate_growing_degree_days(),
            'frost_risk': self.temperature <= WEATHER_CONFIG['ALERT_THRESHOLDS']['LOW_TEMPERATURE'],
            'heat_stress_risk': self.temperature >= WEATHER_CONFIG['ALERT_THRESHOLDS']['HIGH_TEMPERATURE'],
            'disease_risk': (
                self.humidity >= WEATHER_CONFIG['ALERT_THRESHOLDS']['HIGH_HUMIDITY'] and
                self.temperature >= 20
            )
        }
        
    def _calculate_growing_degree_days(self) -> float:
        """Calculate growing degree days."""
        base_temp = WEATHER_CONFIG['GROWING_DEGREE_DAYS']['BASE_TEMPERATURE']
        return max(0, self.temperature - base_temp)

class WeatherForecast(models.Model):
    """
    Weather forecast for a specific location and date.
    
    Attributes:
        location (Location): The location this forecast is for
        forecast_date (date): Date of the forecast
        min_temperature (float): Minimum temperature in Celsius
        max_temperature (float): Maximum temperature in Celsius
        humidity (float): Expected relative humidity
        rainfall_probability (float): Probability of rainfall
        expected_rainfall (float): Expected rainfall amount in mm
        wind_speed (float): Expected wind speed in km/h
        weather_condition (str): Expected weather condition
        confidence_level (float): Forecast confidence percentage
    """
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    forecast_date = models.DateField()
    min_temperature = models.FloatField()
    max_temperature = models.FloatField()
    humidity = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    rainfall_probability = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    expected_rainfall = models.FloatField(
        default=0,
        help_text="Expected rainfall in mm"
    )
    wind_speed = models.FloatField(help_text="Expected wind speed in km/h")
    weather_condition = models.CharField(
        max_length=100,
        choices=[(k, v) for k, v in WEATHER_CONDITIONS.items()]
    )
    frost_risk = models.BooleanField(default=False)
    heat_stress_risk = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    confidence_level = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Forecast confidence level in percentage"
    )

    class Meta:
        indexes = [
            models.Index(fields=['location', 'forecast_date']),
            models.Index(fields=['forecast_date']),
            models.Index(fields=['location', 'weather_condition']),
        ]
        ordering = ['forecast_date']

    def __str__(self) -> str:
        return f"Forecast for {self.location} on {self.forecast_date}"

    def clean(self) -> None:
        """Validate forecast data."""
        super().clean()
        if self.min_temperature > self.max_temperature:
            raise ValidationError({
                'min_temperature': 'Minimum temperature cannot be greater than maximum'
            })
            
        if self.forecast_date < timezone.now().date():
            raise ValidationError({
                'forecast_date': 'Forecast date cannot be in the past'
            })

    def get_average_temperature(self) -> float:
        """Calculate average temperature."""
        return (self.max_temperature + self.min_temperature) / 2

class WeatherAlert(models.Model):
    """
    Weather alert for dangerous or significant weather conditions.
    
    Attributes:
        location (Location): The location this alert is for
        alert_type (str): Type of weather alert
        severity (str): Alert severity level
        description (str): Detailed description of the alert
        recommended_actions (str): Actions farmers should take
        start_time (datetime): When the alert begins
        end_time (datetime): When the alert ends
        is_active (bool): Whether the alert is currently active
        affected_crops (ManyToMany): Crops that may be affected
    """
    
    ALERT_TYPES = [
        ('FROST', 'Frost Warning'),
        ('HEATWAVE', 'Heat Wave'),
        ('HEAVY_RAIN', 'Heavy Rainfall'),
        ('STORM', 'Storm Warning'),
        ('PEST', 'Pest Weather Conditions'),
        ('DISEASE', 'Disease Favorable Weather'),
    ]
    
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('EXTREME', 'Extreme'),
    ]

    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    description = models.TextField()
    recommended_actions = models.TextField(
        help_text="Recommended actions for farmers"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    actual_impact = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    affected_crops = models.ManyToManyField(
        'crops.Crop',
        help_text="Crops that might be affected by this weather condition"
    )

    class Meta:
        indexes = [
            models.Index(fields=['location', 'start_time']),
            models.Index(fields=['is_active']),
            models.Index(fields=['alert_type', 'severity']),
        ]
        ordering = ['-start_time']

    def __str__(self) -> str:
        return f"{self.get_alert_type_display()} alert for {self.location}"

    def clean(self) -> None:
        """Validate alert data."""
        super().clean()
        if self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': 'End time must be after start time'
            })
        
        if self.resolved_at and self.resolved_at < self.start_time:
            raise ValidationError({
                'resolved_at': 'Resolution time cannot be before start time'
            })

    def resolve(self, notes: str = "", impact: str = "") -> None:
        """Mark alert as resolved with optional notes and impact description."""
        self.is_active = False
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.actual_impact = impact
        self.save()

    def get_duration(self) -> Optional[timezone.timedelta]:
        """Calculate alert duration."""
        if self.resolved_at:
            return self.resolved_at - self.start_time
        if not self.is_active:
            return self.end_time - self.start_time
        return None
