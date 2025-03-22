"""
Tests for weather application models.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

from ..models import Location, WeatherData, WeatherForecast, WeatherAlert
from ..config import WEATHER_CONFIG

class LocationModelTests(TestCase):
    def setUp(self):
        self.valid_location_data = {
            'name': 'Test Village',
            'district': 'Test District',
            'state': 'Haryana',
            'latitude': Decimal('28.7041'),
            'longitude': Decimal('77.1025'),
            'elevation': 216.5
        }

    def test_create_valid_location(self):
        """Test creating a location with valid data."""
        location = Location.objects.create(**self.valid_location_data)
        self.assertEqual(str(location), 'Test Village, Test District')
        self.assertEqual(location.state, 'Haryana')

    def test_invalid_coordinates(self):
        """Test validation of invalid coordinates."""
        invalid_data = self.valid_location_data.copy()
        invalid_data['latitude'] = 91  # Invalid latitude
        
        with self.assertRaises(ValidationError):
            location = Location(**invalid_data)
            location.full_clean()

    def test_negative_elevation(self):
        """Test validation of negative elevation."""
        invalid_data = self.valid_location_data.copy()
        invalid_data['elevation'] = -10
        
        with self.assertRaises(ValidationError):
            location = Location(**invalid_data)
            location.full_clean()

    def test_distance_calculation(self):
        """Test Haversine distance calculation."""
        location = Location.objects.create(**self.valid_location_data)
        
        # Calculate distance to another point (approximately 10km away)
        distance = location.get_distance_to(
            Decimal('28.7941'),  # ~10km north
            Decimal('77.1025')
        )
        self.assertAlmostEqual(distance, 10.0, delta=0.5)

class WeatherDataModelTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(
            name='Test Village',
            district='Test District',
            state='Haryana',
            latitude=Decimal('28.7041'),
            longitude=Decimal('77.1025')
        )
        
        self.valid_weather_data = {
            'location': self.location,
            'temperature': 25.5,
            'humidity': 65.0,
            'rainfall': 0.0,
            'wind_speed': 10.5,
            'wind_direction': 180,
            'soil_temperature': 22.5,
            'soil_moisture': 45.0,
            'solar_radiation': 850.0,
            'weather_condition': 'CLEAR',
            'timestamp': timezone.now(),
            'data_source': 'TEST'
        }

    def test_create_valid_weather_data(self):
        """Test creating weather data with valid values."""
        weather = WeatherData.objects.create(**self.valid_weather_data)
        self.assertEqual(weather.location, self.location)
        self.assertEqual(weather.temperature, 25.5)

    def test_invalid_temperature(self):
        """Test validation of invalid temperature."""
        invalid_data = self.valid_weather_data.copy()
        invalid_data['temperature'] = 1000  # Invalid temperature
        
        with self.assertRaises(ValidationError):
            weather = WeatherData(**invalid_data)
            weather.full_clean()

    def test_future_timestamp(self):
        """Test validation of future timestamp."""
        future_data = self.valid_weather_data.copy()
        future_data['timestamp'] = timezone.now() + timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            weather = WeatherData(**future_data)
            weather.full_clean()

    def test_agricultural_metrics(self):
        """Test calculation of agricultural metrics."""
        weather = WeatherData.objects.create(**self.valid_weather_data)
        metrics = weather.get_agricultural_metrics()
        
        self.assertIn('growing_degree_days', metrics)
        self.assertIn('frost_risk', metrics)
        self.assertIn('heat_stress_risk', metrics)
        self.assertIn('disease_risk', metrics)

class WeatherForecastModelTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(
            name='Test Village',
            district='Test District',
            state='Haryana',
            latitude=Decimal('28.7041'),
            longitude=Decimal('77.1025')
        )
        
        self.valid_forecast_data = {
            'location': self.location,
            'forecast_date': timezone.now().date() + timedelta(days=1),
            'min_temperature': 20.0,
            'max_temperature': 30.0,
            'humidity': 65.0,
            'rainfall_probability': 30.0,
            'expected_rainfall': 5.0,
            'wind_speed': 15.0,
            'weather_condition': 'CLEAR',
            'confidence_level': 80.0
        }

    def test_create_valid_forecast(self):
        """Test creating forecast with valid data."""
        forecast = WeatherForecast.objects.create(**self.valid_forecast_data)
        self.assertEqual(forecast.location, self.location)
        self.assertEqual(forecast.get_average_temperature(), 25.0)

    def test_invalid_temperature_range(self):
        """Test validation of invalid temperature range."""
        invalid_data = self.valid_forecast_data.copy()
        invalid_data['min_temperature'] = 35.0  # Higher than max_temperature
        invalid_data['max_temperature'] = 30.0
        
        with self.assertRaises(ValidationError):
            forecast = WeatherForecast(**invalid_data)
            forecast.full_clean()

    def test_past_forecast_date(self):
        """Test validation of past forecast date."""
        past_data = self.valid_forecast_data.copy()
        past_data['forecast_date'] = timezone.now().date() - timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            forecast = WeatherForecast(**past_data)
            forecast.full_clean()

class WeatherAlertModelTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(
            name='Test Village',
            district='Test District',
            state='Haryana',
            latitude=Decimal('28.7041'),
            longitude=Decimal('77.1025')
        )
        
        now = timezone.now()
        self.valid_alert_data = {
            'location': self.location,
            'alert_type': 'FROST',
            'severity': 'HIGH',
            'description': 'Test alert',
            'recommended_actions': 'Take protective measures',
            'start_time': now,
            'end_time': now + timedelta(hours=6)
        }

    def test_create_valid_alert(self):
        """Test creating alert with valid data."""
        alert = WeatherAlert.objects.create(**self.valid_alert_data)
        self.assertEqual(alert.location, self.location)
        self.assertTrue(alert.is_active)

    def test_invalid_time_range(self):
        """Test validation of invalid time range."""
        invalid_data = self.valid_alert_data.copy()
        invalid_data['end_time'] = invalid_data['start_time']  # Same as start_time
        
        with self.assertRaises(ValidationError):
            alert = WeatherAlert(**invalid_data)
            alert.full_clean()

    def test_resolve_alert(self):
        """Test resolving an alert."""
        alert = WeatherAlert.objects.create(**self.valid_alert_data)
        
        resolution_notes = "Alert handled successfully"
        actual_impact = "Minimal crop damage"
        
        alert.resolve(notes=resolution_notes, impact=actual_impact)
        
        self.assertFalse(alert.is_active)
        self.assertIsNotNone(alert.resolved_at)
        self.assertEqual(alert.resolution_notes, resolution_notes)
        self.assertEqual(alert.actual_impact, actual_impact)

    def test_get_duration(self):
        """Test alert duration calculation."""
        alert = WeatherAlert.objects.create(**self.valid_alert_data)
        
        # Test duration for active alert
        self.assertIsNone(alert.get_duration())
        
        # Test duration for resolved alert
        alert.resolve()
        duration = alert.get_duration()
        self.assertIsNotNone(duration)
        self.assertIsInstance(duration, timedelta)