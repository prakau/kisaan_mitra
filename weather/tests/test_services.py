"""
Tests for weather analysis services.
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from ..models import Location, WeatherData, WeatherForecast, WeatherAlert
from ..services import WeatherAnalysisService
from ..config import WEATHER_CONFIG
from ..exceptions import WeatherDataError

class WeatherAnalysisServiceTests(TestCase):
    def setUp(self):
        self.service = WeatherAnalysisService()
        
        # Create test location
        self.location = Location.objects.create(
            name='Test Village',
            district='Test District',
            state='Haryana',
            latitude=Decimal('28.7041'),
            longitude=Decimal('77.1025')
        )
        
        # Create test weather data
        self.current_weather = WeatherData.objects.create(
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
        
        # Create historical weather data
        for i in range(7):
            WeatherData.objects.create(
                location=self.location,
                temperature=25.0 + i,
                humidity=60.0 + i,
                rainfall=i * 2.0,
                wind_speed=10.0,
                wind_direction=180,
                soil_temperature=22.0 + i,
                soil_moisture=40.0 + i,
                weather_condition='CLEAR',
                timestamp=timezone.now() - timedelta(days=i),
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

    def test_calculate_growing_degree_days(self):
        """Test GDD calculation with different temperatures."""
        base_temp = WEATHER_CONFIG['GROWING_DEGREE_DAYS']['BASE_TEMPERATURE']
        
        # Test normal temperature
        gdd = self.service.calculate_growing_degree_days(25.0)
        self.assertEqual(gdd, 25.0 - base_temp)
        
        # Test temperature below base
        gdd = self.service.calculate_growing_degree_days(5.0)
        self.assertEqual(gdd, 0)
        
        # Test with custom base temperature
        gdd = self.service.calculate_growing_degree_days(25.0, base_temp=15.0)
        self.assertEqual(gdd, 10.0)

    def test_assess_crop_suitability(self):
        """Test crop suitability assessment."""
        from crops.models import Crop
        
        # Create test crop
        crop = Crop.objects.create(
            name='Test Crop',
            min_temp=20.0,
            max_temp=30.0,
            min_humidity=50.0,
            max_humidity=80.0,
            min_soil_moisture=30.0,
            max_soil_moisture=70.0
        )
        
        assessment = self.service.assess_crop_suitability(
            self.current_weather,
            crop
        )
        
        self.assertIn('temperature_suitable', assessment)
        self.assertIn('humidity_suitable', assessment)
        self.assertIn('soil_moisture_suitable', assessment)
        self.assertIn('risk_factors', assessment)
        
        # Test with unsuitable conditions
        unsuitable_weather = WeatherData.objects.create(
            location=self.location,
            temperature=35.0,  # Too hot
            humidity=90.0,  # Too humid
            rainfall=0.0,
            wind_speed=10.0,
            wind_direction=180,
            soil_moisture=80.0,  # Too wet
            weather_condition='CLEAR',
            timestamp=timezone.now(),
            data_source='TEST'
        )
        
        assessment = self.service.assess_crop_suitability(
            unsuitable_weather,
            crop
        )
        
        self.assertFalse(assessment['temperature_suitable'])
        self.assertFalse(assessment['humidity_suitable'])
        self.assertFalse(assessment['soil_moisture_suitable'])
        self.assertTrue(len(assessment['risk_factors']) > 0)

    def test_get_agricultural_metrics(self):
        """Test agricultural metrics calculation."""
        metrics = self.service.get_agricultural_metrics(self.location.id)
        
        self.assertIn('current_conditions', metrics)
        self.assertIn('historical_analysis', metrics)
        self.assertIn('agricultural_alerts', metrics)
        
        current = metrics['current_conditions']
        self.assertIn('frost_risk', current)
        self.assertIn('heat_stress_risk', current)
        self.assertIn('disease_risk', current)
        self.assertIn('soil_conditions', current)
        
        # Test with no weather data
        WeatherData.objects.all().delete()
        with self.assertRaises(WeatherDataError):
            self.service.get_agricultural_metrics(self.location.id)

    def test_analyze_forecast_implications(self):
        """Test forecast analysis."""
        analysis = self.service.analyze_forecast_implications(self.forecast)
        
        self.assertIn('general_conditions', analysis)
        self.assertIn('agricultural_risks', analysis)
        self.assertIn('recommendations', analysis)
        
        # Test with crop-specific analysis
        from crops.models import Crop
        crop = Crop.objects.create(
            name='Test Crop',
            min_temp=20.0,
            max_temp=30.0,
            min_humidity=50.0,
            max_humidity=80.0
        )
        
        analysis = self.service.analyze_forecast_implications(
            self.forecast,
            crop_id=crop.id
        )
        
        self.assertIn('crop_specific', analysis)
        
        # Test with extreme conditions
        extreme_forecast = WeatherForecast.objects.create(
            location=self.location,
            forecast_date=timezone.now().date() + timedelta(days=1),
            min_temperature=0.0,  # Very cold
            max_temperature=40.0,  # Very hot
            humidity=90.0,  # Very humid
            rainfall_probability=80.0,
            weather_condition='STORM',
            confidence_level=80.0
        )
        
        analysis = self.service.analyze_forecast_implications(extreme_forecast)
        risks = analysis['agricultural_risks']
        self.assertTrue(risks.get('frost_risk'))
        self.assertTrue(risks.get('heat_stress_risk'))
        self.assertIn('STORM', analysis['recommendations'])

    def test_historical_trend_analysis(self):
        """Test analysis of historical weather patterns."""
        metrics = self.service.get_agricultural_metrics(self.location.id)
        historical = metrics['historical_analysis']
        
        self.assertIn('temperature_trends', historical)
        self.assertIn('rainfall_patterns', historical)
        self.assertIn('soil_moisture_trends', historical)
        
        temperature_trends = historical['temperature_trends']
        self.assertIn('average', temperature_trends)
        self.assertIn('trend', temperature_trends)
        self.assertIn('extremes', temperature_trends)
        
        rainfall = historical['rainfall_patterns']
        self.assertIn('total', rainfall)
        self.assertIn('average', rainfall)
        self.assertIn('days_with_rain', rainfall)
        
        # Verify increasing temperature trend
        self.assertEqual(temperature_trends['trend'], 'increasing')