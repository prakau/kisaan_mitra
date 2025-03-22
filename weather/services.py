"""
Service layer for weather-related business logic and analysis.
Implements complex calculations and data processing operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg

from .models import WeatherData, WeatherForecast, Crop
from .repositories import WeatherRepository
from .config import WEATHER_CONFIG
from .exceptions import WeatherDataError

class WeatherAnalysisService:
    """Handles weather data analysis and agricultural insights."""
    
    def __init__(self):
        self.repository = WeatherRepository()

    def calculate_growing_degree_days(
        self, 
        temperature: float,
        base_temp: float = WEATHER_CONFIG['GROWING_DEGREE_DAYS']['BASE_TEMPERATURE']
    ) -> float:
        """
        Calculate growing degree days (GDD) for crop development tracking.
        GDD = max(0, average_temp - base_temp)
        """
        return max(0, temperature - base_temp)

    def assess_crop_suitability(
        self, 
        weather_data: WeatherData, 
        crop: Crop
    ) -> Dict[str, Any]:
        """Assess weather conditions' suitability for a specific crop."""
        return {
            'temperature_suitable': (
                crop.min_temp <= weather_data.temperature <= crop.max_temp
            ),
            'humidity_suitable': (
                crop.min_humidity <= weather_data.humidity <= crop.max_humidity
            ),
            'soil_moisture_suitable': (
                weather_data.soil_moisture and
                crop.min_soil_moisture <= weather_data.soil_moisture <= crop.max_soil_moisture
            ),
            'risk_factors': self._analyze_risk_factors(weather_data, crop)
        }

    def get_agricultural_metrics(
        self, 
        location_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Calculate agricultural metrics for a location."""
        weather_data = self.repository.get_weather_history(location_id, days)
        
        if not weather_data:
            raise WeatherDataError("No weather data available")
            
        current = self.repository.get_current_weather(location_id)
        
        metrics = {
            'current_conditions': self._analyze_current_conditions(current),
            'historical_analysis': self._analyze_historical_data(weather_data),
            'agricultural_alerts': self._generate_agricultural_alerts(current, weather_data)
        }
        
        return metrics

    def analyze_forecast_implications(
        self,
        forecast: WeatherForecast,
        crop_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Analyze forecast implications for agriculture."""
        analysis = {
            'general_conditions': self._analyze_forecast_conditions(forecast),
            'agricultural_risks': self._analyze_forecast_risks(forecast),
            'recommendations': self._generate_recommendations(forecast)
        }
        
        if crop_id:
            try:
                crop = Crop.objects.get(id=crop_id)
                analysis['crop_specific'] = self._analyze_crop_specific_impacts(
                    forecast, crop
                )
            except Crop.DoesNotExist:
                pass
                
        return analysis

    def _analyze_current_conditions(self, weather: WeatherData) -> Dict[str, Any]:
        """Analyze current weather conditions."""
        return {
            'frost_risk': weather.temperature <= WEATHER_CONFIG['ALERT_THRESHOLDS']['LOW_TEMPERATURE'],
            'heat_stress_risk': weather.temperature >= WEATHER_CONFIG['ALERT_THRESHOLDS']['HIGH_TEMPERATURE'],
            'disease_risk': (
                weather.humidity >= WEATHER_CONFIG['ALERT_THRESHOLDS']['HIGH_HUMIDITY'] and
                weather.temperature >= 20
            ),
            'soil_conditions': {
                'moisture_status': self._assess_soil_moisture(weather.soil_moisture),
                'temperature_status': self._assess_soil_temperature(weather.soil_temperature)
            }
        }

    def _analyze_historical_data(self, weather_data: List[Dict]) -> Dict[str, Any]:
        """Analyze historical weather patterns."""
        if not weather_data:
            return {}
            
        return {
            'temperature_trends': self._analyze_temperature_trends(weather_data),
            'rainfall_patterns': self._analyze_rainfall_patterns(weather_data),
            'soil_moisture_trends': self._analyze_soil_moisture_trends(weather_data)
        }

    def _analyze_risk_factors(
        self,
        weather: WeatherData,
        crop: Crop
    ) -> List[str]:
        """Identify potential risk factors for a crop."""
        risks = []
        
        if weather.temperature <= crop.min_temp:
            risks.append("Cold stress risk")
        if weather.temperature >= crop.max_temp:
            risks.append("Heat stress risk")
        if weather.humidity >= WEATHER_CONFIG['ALERT_THRESHOLDS']['HIGH_HUMIDITY']:
            risks.append("Disease risk due to high humidity")
        if weather.soil_moisture and weather.soil_moisture < crop.min_soil_moisture:
            risks.append("Drought stress risk")
            
        return risks

    def _assess_soil_moisture(self, moisture: Optional[float]) -> str:
        """Assess soil moisture status."""
        if moisture is None:
            return "unknown"
            
        if moisture < WEATHER_CONFIG['ALERT_THRESHOLDS']['LOW_SOIL_MOISTURE']:
            return "dry"
        if moisture > WEATHER_CONFIG['ALERT_THRESHOLDS']['HIGH_SOIL_MOISTURE']:
            return "saturated"
        return "optimal"

    def _assess_soil_temperature(self, temperature: Optional[float]) -> str:
        """Assess soil temperature status."""
        if temperature is None:
            return "unknown"
            
        if temperature < 10:
            return "cold"
        if temperature > 35:
            return "hot"
        return "optimal"

    def _analyze_temperature_trends(self, weather_data: List[Dict]) -> Dict[str, Any]:
        """Analyze temperature patterns over time."""
        temps = [day['avg_temp'] for day in weather_data if day['avg_temp'] is not None]
        if not temps:
            return {}
            
        return {
            'average': sum(temps) / len(temps),
            'trend': self._calculate_trend(temps),
            'extremes': {
                'high': max(temps),
                'low': min(temps)
            }
        }

    def _analyze_rainfall_patterns(self, weather_data: List[Dict]) -> Dict[str, Any]:
        """Analyze rainfall patterns."""
        rainfall = [day['total_rainfall'] for day in weather_data if day['total_rainfall'] is not None]
        if not rainfall:
            return {}
            
        return {
            'total': sum(rainfall),
            'average': sum(rainfall) / len(rainfall),
            'days_with_rain': sum(1 for r in rainfall if r > 0),
            'trend': self._calculate_trend(rainfall)
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 2:
            return "stable"
            
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff = second_half - first_half
        if abs(diff) < 0.1:  # threshold for considering trend significant
            return "stable"
        return "increasing" if diff > 0 else "decreasing"

    def _generate_agricultural_alerts(
        self,
        current: WeatherData,
        historical: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate agricultural alerts based on weather conditions."""
        alerts = []
        
        # Check current conditions
        if current.temperature <= WEATHER_CONFIG['ALERT_THRESHOLDS']['LOW_TEMPERATURE']:
            alerts.append({
                'type': 'frost_risk',
                'severity': 'high',
                'message': 'Risk of frost damage to crops'
            })
            
        if current.temperature >= WEATHER_CONFIG['ALERT_THRESHOLDS']['HIGH_TEMPERATURE']:
            alerts.append({
                'type': 'heat_stress',
                'severity': 'high',
                'message': 'Risk of heat stress to crops'
            })
            
        # Check soil moisture
        if current.soil_moisture and current.soil_moisture < WEATHER_CONFIG['ALERT_THRESHOLDS']['LOW_SOIL_MOISTURE']:
            alerts.append({
                'type': 'low_soil_moisture',
                'severity': 'medium',
                'message': 'Soil moisture below optimal level'
            })
            
        return alerts