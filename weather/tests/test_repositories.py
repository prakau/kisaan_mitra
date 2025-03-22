"""
Tests for weather data repositories.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from ..models import Location, WeatherData, WeatherForecast, WeatherAlert
from ..repositories import WeatherRepository
from ..exceptions import InvalidLocationError
from ..config import WEATHER_CONFIG

class WeatherRepositoryTests(TestCase):
    def setUp(self):
        self.repository = WeatherRepository()
        
        # Create test location
        self.location = Location.objects.create(
            name='Test Village',
            district='Test District',
            state='Haryana',
            latitude=Decimal('28.7041'),
            longitude=Decimal('77.1025')
        )
        
        # Create test weather data
        self.weather = WeatherData.objects.create(
            location=self.location,
            temperature=25.5,
            humidity=65.0,
            rainfall=0.0,
            wind_speed=10.5,
            wind_direction=180,
            soil_temperature=22.5,
            soil_moisture=45.0,
            solar_radiation=850.0,
            weather_condition='CLEAR',
            timestamp=timezone.now(),
            data_source='TEST'
        )
        
        # Create test forecast
        self.forecast = WeatherForecast.objects.create(
            location=self.location,
            forecast_date=timezone.now().date() + timedelta(days=1),
            min_temperature=20.0,
            max_temperature=30.0,
            humidity=65.0,
            rainfall_probability=30.0,
            expected_rainfall=5.0,
            wind_speed=15.0,
            weather_condition='CLEAR',
            confidence_level=80.0
        )
        
        # Create test alert
        self.alert = WeatherAlert.objects.create(
            location=self.location,
            alert_type='FROST',
            severity='HIGH',
            description='Test alert',
            recommended_actions='Take protective measures',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=6)
        )

    def tearDown(self):
        cache.clear()

    def test_get_location(self):
        """Test retrieving location with caching."""
        # First call should hit database
        location = self.repository.get_location(self.location.id)
        self.assertEqual(location, self.location)
        
        # Second call should hit cache
        location = self.repository.get_location(self.location.id)
        self.assertEqual(location, self.location)
        
        with self.assertRaises(InvalidLocationError):
            self.repository.get_location(999)  # Non-existent ID

    def test_get_current_weather(self):
        """Test retrieving current weather data."""
        weather = self.repository.get_current_weather(self.location.id)
        self.assertEqual(weather, self.weather)
        
        # Test with old weather data
        self.weather.timestamp = timezone.now() - timedelta(days=1)
        self.weather.save()
        weather = self.repository.get_current_weather(self.location.id)
        self.assertIsNone(weather)

    def test_get_weather_history(self):
        """Test retrieving historical weather data."""
        # Create some historical data
        old_weather = WeatherData.objects.create(
            location=self.location,
            temperature=24.0,
            humidity=60.0,
            rainfall=10.0,
            wind_speed=12.0,
            wind_direction=90,
            weather_condition='RAIN',
            timestamp=timezone.now() - timedelta(days=2),
            data_source='TEST'
        )
        
        history = self.repository.get_weather_history(
            self.location.id,
            days=3
        )
        self.assertEqual(len(history), 2)  # Should include both records

    def test_get_active_alerts(self):
        """Test retrieving active alerts."""
        alerts = self.repository.get_active_alerts(self.location.id)
        self.assertEqual(len(alerts), 1)
        
        # Test with resolved alert
        self.alert.is_active = False
        self.alert.save()
        alerts = self.repository.get_active_alerts(self.location.id)
        self.assertEqual(len(alerts), 0)

    def test_get_weather_forecast(self):
        """Test retrieving weather forecasts."""
        forecasts = self.repository.get_weather_forecast(self.location.id)
        self.assertEqual(len(forecasts), 1)
        
        # Test with max days limit
        max_days = WEATHER_CONFIG['MAX_FORECAST_DAYS']
        forecasts = self.repository.get_weather_forecast(
            self.location.id,
            days=max_days + 1
        )
        self.assertTrue(len(forecasts) <= max_days)

    def test_get_nearby_locations(self):
        """Test finding nearby locations."""
        # Create another location ~10km away
        nearby_location = Location.objects.create(
            name='Nearby Village',
            district='Test District',
            state='Haryana',
            latitude=Decimal('28.7941'),  # ~10km north
            longitude=Decimal('77.1025')
        )
        
        # Create a far location
        far_location = Location.objects.create(
            name='Far Village',
            district='Test District',
            state='Haryana',
            latitude=Decimal('29.7041'),  # ~100km north
            longitude=Decimal('77.1025')
        )
        
        locations = list(self.repository.get_nearby_locations(
            float(self.location.latitude),
            float(self.location.longitude),
            radius_km=15
        ))
        
        self.assertEqual(len(locations), 2)  # Should include original and nearby
        self.assertIn(self.location, locations)
        self.assertIn(nearby_location, locations)
        self.assertNotIn(far_location, locations)

    def test_create_weather_data(self):
        """Test creating new weather data."""
        new_data = {
            'location': self.location,
            'temperature': 26.5,
            'humidity': 70.0,
            'rainfall': 0.0,
            'wind_speed': 12.5,
            'wind_direction': 90,
            'weather_condition': 'CLEAR',
            'timestamp': timezone.now(),
            'data_source': 'TEST'
        }
        
        weather = self.repository.create_weather_data(new_data)
        self.assertEqual(weather.temperature, 26.5)
        
        # Test validation
        invalid_data = new_data.copy()
        invalid_data['temperature'] = 1000  # Invalid temperature
        with self.assertRaises(WeatherDataValidationError):
            self.repository.create_weather_data(invalid_data)

    def test_create_weather_alert(self):
        """Test creating new weather alert."""
        new_data = {
            'location': self.location,
            'alert_type': 'HEATWAVE',
            'severity': 'HIGH',
            'description': 'Test alert',
            'recommended_actions': 'Stay hydrated',
            'start_time': timezone.now(),
            'end_time': timezone.now() + timedelta(hours=12)
        }
        
        alert = self.repository.create_weather_alert(new_data, [])
        self.assertEqual(alert.alert_type, 'HEATWAVE')