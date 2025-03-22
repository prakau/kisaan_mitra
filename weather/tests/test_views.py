"""
Tests for weather application views.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta

from ..models import Location, WeatherData, WeatherForecast, WeatherAlert
from . import (
    TEST_LOCATION_DATA,
    TEST_WEATHER_DATA,
    TEST_FORECAST_DATA,
    TEST_ALERT_DATA,
    create_test_data_sequence
)

User = get_user_model()

class WeatherViewsTestCase(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test location
        self.location = Location.objects.create(**TEST_LOCATION_DATA)
        
        # Create test weather data
        weather_data = TEST_WEATHER_DATA.copy()
        weather_data['location'] = self.location
        self.weather = WeatherData.objects.create(**weather_data)
        
        # Create test forecast
        forecast_data = TEST_FORECAST_DATA.copy()
        forecast_data['location'] = self.location
        self.forecast = WeatherForecast.objects.create(**forecast_data)
        
        # Create test alert
        alert_data = TEST_ALERT_DATA.copy()
        alert_data['location'] = self.location
        self.alert = WeatherAlert.objects.create(**alert_data)

class LocationViewSetTests(WeatherViewsTestCase):
    def test_list_locations(self):
        """Test retrieving location list."""
        url = reverse('location-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.location.name)

    def test_create_location(self):
        """Test creating a new location."""
        url = reverse('location-list')
        new_location_data = {
            'name': 'New Village',
            'district': 'New District',
            'state': 'Haryana',
            'latitude': '28.9',
            'longitude': '77.2'
        }
        
        response = self.client.post(url, new_location_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Location.objects.count(), 2)

    def test_nearby_locations(self):
        """Test finding nearby locations."""
        # Create another location ~10km away
        Location.objects.create(
            name='Nearby Village',
            district='Test District',
            state='Haryana',
            latitude=Decimal('28.7941'),
            longitude=Decimal('77.1025')
        )
        
        url = reverse('location-nearby')
        response = self.client.get(url, {
            'latitude': str(self.location.latitude),
            'longitude': str(self.location.longitude),
            'radius': '15'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

class WeatherDataViewSetTests(WeatherViewsTestCase):
    def test_list_weather_data(self):
        """Test retrieving weather data list."""
        url = reverse('weatherdata-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_current_weather(self):
        """Test retrieving current weather."""
        url = reverse('weatherdata-current')
        response = self.client.get(url, {'location_id': self.location.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['temperature'], self.weather.temperature)
        self.assertIn('agricultural_metrics', response.data)

    def test_historical_weather(self):
        """Test retrieving historical weather data."""
        # Create historical data
        weather_sequence = create_test_data_sequence(
            TEST_WEATHER_DATA,
            days=7
        )
        for data in weather_sequence:
            data['location'] = self.location
            WeatherData.objects.create(**data)
            
        url = reverse('weatherdata-historical')
        response = self.client.get(url, {
            'location_id': self.location.id,
            'days': 7
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('daily_statistics', response.data)
        self.assertIn('period_summary', response.data)

class WeatherForecastViewSetTests(WeatherViewsTestCase):
    def test_list_forecasts(self):
        """Test retrieving forecast list."""
        url = reverse('weatherforecast-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_weekly_forecast(self):
        """Test retrieving weekly forecast."""
        url = reverse('weatherforecast-weekly')
        response = self.client.get(url, {
            'location_id': self.location.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertIn('agricultural_risks', response.data[0])

    def test_monthly_outlook(self):
        """Test retrieving monthly outlook."""
        # Create forecast sequence
        forecast_sequence = create_test_data_sequence(
            TEST_FORECAST_DATA,
            days=30
        )
        for data in forecast_sequence:
            data['location'] = self.location
            WeatherForecast.objects.create(**data)
            
        url = reverse('weatherforecast-monthly-outlook')
        response = self.client.get(url, {
            'location_id': self.location.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('weekly_outlook', response.data)
        self.assertIn('monthly_summary', response.data)

class WeatherAlertViewSetTests(WeatherViewsTestCase):
    def test_list_alerts(self):
        """Test retrieving alert list."""
        url = reverse('weatheralert-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_active_alerts(self):
        """Test retrieving active alerts."""
        url = reverse('weatheralert-active')
        response = self.client.get(url, {
            'location_id': self.location.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('impact_assessment', response.data[0])

    def test_resolve_alert(self):
        """Test resolving an alert."""
        url = reverse('weatheralert-resolve', kwargs={'pk': self.alert.pk})
        response = self.client.post(url, {
            'resolution_notes': 'Test resolution',
            'actual_impact': 'Minimal impact'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alert.refresh_from_db()
        self.assertFalse(self.alert.is_active)

class LocationWeatherViewSetTests(WeatherViewsTestCase):
    def test_comprehensive_weather_info(self):
        """Test retrieving comprehensive weather information."""
        url = reverse('location-weather-list')
        response = self.client.get(url, {
            'location_id': self.location.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('location', response.data)
        self.assertIn('current_weather', response.data)
        self.assertIn('forecasts', response.data)
        self.assertIn('active_alerts', response.data)
        self.assertIn('agricultural_summary', response.data)

    def test_error_handling(self):
        """Test error handling for invalid location."""
        url = reverse('location-weather-list')
        response = self.client.get(url, {
            'location_id': 999  # Non-existent location
        })
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('weatherdata-list')

    def test_authentication_required(self):
        """Test that authentication is required for API access."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access(self):
        """Test access with authenticated user."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)