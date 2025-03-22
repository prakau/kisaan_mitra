"""
Tests for weather application serializers.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from ..models import Location, WeatherData, WeatherForecast, WeatherAlert
from ..serializers import (
    LocationSerializer,
    WeatherDataSerializer,
    WeatherForecastSerializer,
    WeatherAlertSerializer,
    LocationWeatherSerializer,
    WeatherStatsSerializer,
    HistoricalWeatherSerializer
)
from . import (
    TEST_LOCATION_DATA,
    TEST_WEATHER_DATA,
    TEST_FORECAST_DATA,
    TEST_ALERT_DATA
)

class LocationSerializerTests(TestCase):
    def test_serialization(self):
        """Test location serialization."""
        location = Location.objects.create(**TEST_LOCATION_DATA)
        serializer = LocationSerializer(location)
        data = serializer.data
        
        self.assertEqual(data['name'], TEST_LOCATION_DATA['name'])
        self.assertEqual(data['district'], TEST_LOCATION_DATA['district'])
        self.assertEqual(data['state'], TEST_LOCATION_DATA['state'])
        self.assertEqual(Decimal(data['latitude']), TEST_LOCATION_DATA['latitude'])
        self.assertEqual(Decimal(data['longitude']), TEST_LOCATION_DATA['longitude'])

    def test_validation(self):
        """Test location data validation."""
        # Test invalid coordinates
        invalid_data = TEST_LOCATION_DATA.copy()
        invalid_data['latitude'] = 91  # Invalid latitude
        
        serializer = LocationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('latitude', serializer.errors)

class WeatherDataSerializerTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(**TEST_LOCATION_DATA)
        self.weather_data = TEST_WEATHER_DATA.copy()
        self.weather_data['location'] = self.location
        self.weather = WeatherData.objects.create(**self.weather_data)

    def test_serialization(self):
        """Test weather data serialization."""
        serializer = WeatherDataSerializer(self.weather)
        data = serializer.data
        
        self.assertEqual(data['temperature'], self.weather_data['temperature'])
        self.assertEqual(data['humidity'], self.weather_data['humidity'])
        self.assertEqual(data['weather_condition'], self.weather_data['weather_condition'])
        self.assertIn('agricultural_metrics', data)

    def test_agricultural_metrics(self):
        """Test agricultural metrics in serialized data."""
        serializer = WeatherDataSerializer(self.weather)
        metrics = serializer.data['agricultural_metrics']
        
        self.assertIn('frost_risk', metrics)
        self.assertIn('heat_stress_risk', metrics)
        self.assertIn('disease_favorable', metrics)
        self.assertIn('soil_condition', metrics)

class WeatherForecastSerializerTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(**TEST_LOCATION_DATA)
        self.forecast_data = TEST_FORECAST_DATA.copy()
        self.forecast_data['location'] = self.location
        self.forecast = WeatherForecast.objects.create(**self.forecast_data)

    def test_serialization(self):
        """Test forecast serialization."""
        serializer = WeatherForecastSerializer(self.forecast)
        data = serializer.data
        
        self.assertEqual(data['min_temperature'], self.forecast_data['min_temperature'])
        self.assertEqual(data['max_temperature'], self.forecast_data['max_temperature'])
        self.assertEqual(data['weather_condition'], self.forecast_data['weather_condition'])
        self.assertIn('agricultural_conditions', data)

    def test_agricultural_conditions(self):
        """Test agricultural conditions in serialized data."""
        serializer = WeatherForecastSerializer(self.forecast)
        conditions = serializer.data['agricultural_conditions']
        
        self.assertIn('growing_conditions', conditions)
        self.assertIn('risks', conditions)
        self.assertIn('irrigation_recommendation', conditions)

class WeatherAlertSerializerTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(**TEST_LOCATION_DATA)
        self.alert_data = TEST_ALERT_DATA.copy()
        self.alert_data['location'] = self.location
        self.alert = WeatherAlert.objects.create(**self.alert_data)

    def test_serialization(self):
        """Test alert serialization."""
        serializer = WeatherAlertSerializer(self.alert)
        data = serializer.data
        
        self.assertEqual(data['alert_type'], self.alert_data['alert_type'])
        self.assertEqual(data['severity'], self.alert_data['severity'])
        self.assertIn('severity_display', data)
        self.assertIn('alert_type_display', data)

    def test_affected_crops(self):
        """Test affected crops serialization."""
        from crops.models import Crop
        crop = Crop.objects.create(name='Test Crop')
        self.alert.affected_crops.add(crop)
        
        serializer = WeatherAlertSerializer(self.alert)
        self.assertIn(crop.name, serializer.data['affected_crops'])

class LocationWeatherSerializerTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(**TEST_LOCATION_DATA)
        
        # Create current weather
        weather_data = TEST_WEATHER_DATA.copy()
        weather_data['location'] = self.location
        self.weather = WeatherData.objects.create(**weather_data)
        
        # Create forecast
        forecast_data = TEST_FORECAST_DATA.copy()
        forecast_data['location'] = self.location
        self.forecast = WeatherForecast.objects.create(**forecast_data)
        
        # Create alert
        alert_data = TEST_ALERT_DATA.copy()
        alert_data['location'] = self.location
        self.alert = WeatherAlert.objects.create(**alert_data)

    def test_comprehensive_serialization(self):
        """Test comprehensive weather information serialization."""
        data = {
            'location': self.location,
            'current_weather': self.weather,
            'forecasts': [self.forecast],
            'active_alerts': [self.alert],
            'historical_context': {
                'avg_temp': 25.0,
                'total_rainfall': 10.0
            },
            'agricultural_summary': {
                'frost_risk': False,
                'heat_stress_risk': False
            }
        }
        
        serializer = LocationWeatherSerializer(data)
        serialized_data = serializer.data
        
        self.assertIn('location', serialized_data)
        self.assertIn('current_weather', serialized_data)
        self.assertIn('forecasts', serialized_data)
        self.assertIn('active_alerts', serialized_data)
        self.assertIn('historical_context', serialized_data)
        self.assertIn('agricultural_summary', serialized_data)