"""
Pytest configuration and fixtures for weather application tests.
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from ..models import Location, WeatherData, WeatherForecast, WeatherAlert
from ..repositories import WeatherRepository
from ..services import WeatherAnalysisService
from . import (
    TEST_LOCATION_DATA,
    TEST_WEATHER_DATA,
    TEST_FORECAST_DATA,
    TEST_ALERT_DATA
)

User = get_user_model()

@pytest.fixture
def test_user():
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123'
    )

@pytest.fixture
def api_client(test_user):
    """Create an authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=test_user)
    return client

@pytest.fixture
def test_location():
    """Create a test location."""
    return Location.objects.create(**TEST_LOCATION_DATA)

@pytest.fixture
def test_weather(test_location):
    """Create test weather data."""
    weather_data = TEST_WEATHER_DATA.copy()
    weather_data['location'] = test_location
    return WeatherData.objects.create(**weather_data)

@pytest.fixture
def test_forecast(test_location):
    """Create test weather forecast."""
    forecast_data = TEST_FORECAST_DATA.copy()
    forecast_data['location'] = test_location
    return WeatherForecast.objects.create(**forecast_data)

@pytest.fixture
def test_alert(test_location):
    """Create test weather alert."""
    alert_data = TEST_ALERT_DATA.copy()
    alert_data['location'] = test_location
    return WeatherAlert.objects.create(**alert_data)

@pytest.fixture
def weather_repository():
    """Create a weather repository instance."""
    return WeatherRepository()

@pytest.fixture
def weather_service():
    """Create a weather analysis service instance."""
    return WeatherAnalysisService()

@pytest.fixture
def historical_weather_data(test_location):
    """Create a sequence of historical weather data."""
    data = []
    for i in range(7):
        weather = WeatherData.objects.create(
            location=test_location,
            temperature=25.0 + i,
            humidity=60.0 + i,
            rainfall=i * 2.0,
            wind_speed=10.0,
            wind_direction=180,
            soil_temperature=22.0 + i,
            soil_moisture=40.0 + i,
            weather_condition='CLEAR',
            timestamp=timezone.now() - timezone.timedelta(days=i),
            data_source='TEST'
        )
        data.append(weather)
    return data

@pytest.fixture
def forecast_sequence(test_location):
    """Create a sequence of weather forecasts."""
    forecasts = []
    for i in range(7):
        forecast = WeatherForecast.objects.create(
            location=test_location,
            forecast_date=timezone.now().date() + timezone.timedelta(days=i),
            min_temperature=20.0 + i,
            max_temperature=30.0 + i,
            humidity=65.0,
            rainfall_probability=30.0,
            expected_rainfall=5.0,
            wind_speed=15.0,
            weather_condition='CLEAR',
            confidence_level=80.0
        )
        forecasts.append(forecast)
    return forecasts

@pytest.fixture
def active_alerts(test_location):
    """Create a set of active weather alerts."""
    alerts = []
    alert_types = ['FROST', 'HEATWAVE', 'HEAVY_RAIN']
    severities = ['LOW', 'MEDIUM', 'HIGH']
    
    for alert_type, severity in zip(alert_types, severities):
        alert = WeatherAlert.objects.create(
            location=test_location,
            alert_type=alert_type,
            severity=severity,
            description=f'Test {alert_type} alert',
            recommended_actions=f'Handle {alert_type} conditions',
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=6)
        )
        alerts.append(alert)
    return alerts

@pytest.fixture
def cleanup_cache():
    """Clean up cache after tests."""
    from django.core.cache import cache
    yield
    cache.clear()