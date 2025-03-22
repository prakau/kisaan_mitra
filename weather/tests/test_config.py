"""
Test configuration and utilities for weather application tests.
"""

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Test location data
TEST_LOCATION_DATA = {
    'name': 'Test Village',
    'district': 'Test District',
    'state': 'Haryana',
    'latitude': Decimal('28.7041'),
    'longitude': Decimal('77.1025'),
    'elevation': 216.5
}

# Test weather data
TEST_WEATHER_DATA = {
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

# Test forecast data
TEST_FORECAST_DATA = {
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

# Test alert data
TEST_ALERT_DATA = {
    'alert_type': 'FROST',
    'severity': 'HIGH',
    'description': 'Test alert',
    'recommended_actions': 'Take protective measures',
    'start_time': timezone.now(),
    'end_time': timezone.now() + timedelta(hours=6)
}

# Test crop data
TEST_CROP_DATA = {
    'name': 'Test Crop',
    'min_temp': 20.0,
    'max_temp': 30.0,
    'min_humidity': 50.0,
    'max_humidity': 80.0,
    'min_soil_moisture': 30.0,
    'max_soil_moisture': 70.0
}

def create_test_data_sequence(base_data: dict, days: int, modifier_func=None) -> list:
    """
    Create a sequence of test data with modifications over time.
    
    Args:
        base_data: Base dictionary of data
        days: Number of days to generate data for
        modifier_func: Optional function to modify data for each day
        
    Returns:
        List of modified data dictionaries
    """
    data_sequence = []
    for i in range(days):
        day_data = base_data.copy()
        if modifier_func:
            day_data = modifier_func(day_data, i)
        if 'timestamp' in day_data:
            day_data['timestamp'] = timezone.now() - timedelta(days=i)
        if 'forecast_date' in day_data:
            day_data['forecast_date'] = timezone.now().date() + timedelta(days=i)
        data_sequence.append(day_data)
    return data_sequence

def default_weather_modifier(data: dict, day: int) -> dict:
    """Default modifier for weather data sequence."""
    data = data.copy()
    data['temperature'] = data['temperature'] + day
    data['humidity'] = min(100, data['humidity'] + day)
    data['rainfall'] = day * 2.0
    return data