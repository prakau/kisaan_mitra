"""
Utilities for handling multilingual weather information.
Supports Hindi, Haryanvi, and English translations.
"""

from typing import Dict, Any, Optional
from django.conf import settings
from django.utils.translation import gettext as _

from .config import WEATHER_CONFIG, WEATHER_CONDITIONS

class WeatherTranslator:
    """
    Handles translation of weather-related information into local languages.
    Supports Hindi, Haryanvi, and English.
    """

    TEMPERATURE_RANGES = {
        'VERY_COLD': {
            'en': 'Very Cold',
            'hi': 'बहुत ठंडा',
            'hr': 'बहुत ठंडा'
        },
        'COLD': {
            'en': 'Cold',
            'hi': 'ठंडा',
            'hr': 'ठंडा'
        },
        'MODERATE': {
            'en': 'Moderate',
            'hi': 'सामान्य',
            'hr': 'ठीक'
        },
        'WARM': {
            'en': 'Warm',
            'hi': 'गरम',
            'hr': 'गरम'
        },
        'HOT': {
            'en': 'Hot',
            'hi': 'बहुत गरम',
            'hr': 'तपत'
        }
    }

    SOIL_CONDITIONS = {
        'DRY': {
            'en': 'Dry soil - irrigation needed',
            'hi': 'सूखी मिट्टी - सिंचाई की आवश्यकता है',
            'hr': 'सूखी माटी - पानी की जरूरत है'
        },
        'MOIST': {
            'en': 'Good soil moisture',
            'hi': 'अच्छी नमी',
            'hr': 'बढ़िया नमी'
        },
        'WET': {
            'en': 'Wet soil - avoid irrigation',
            'hi': 'गीली मिट्टी - सिंचाई न करें',
            'hr': 'गीली माटी - पानी ना दें'
        }
    }

    ALERT_TYPES = {
        'FROST': {
            'en': 'Frost Warning',
            'hi': 'पाला चेतावनी',
            'hr': 'पाला की चेतावनी'
        },
        'HEATWAVE': {
            'en': 'Heat Wave Warning',
            'hi': 'लू की चेतावनी',
            'hr': 'लू की चेतावनी'
        },
        'HEAVY_RAIN': {
            'en': 'Heavy Rain Warning',
            'hi': 'भारी बारिश की चेतावनी',
            'hr': 'तेज बरखा की चेतावनी'
        },
        'PEST_RISK': {
            'en': 'High Pest Risk',
            'hi': 'कीट का खतरा',
            'hr': 'कीड़े का खतरा'
        },
        'DISEASE_RISK': {
            'en': 'Disease Risk',
            'hi': 'बीमारी का खतरा',
            'hr': 'बीमारी का खतरा'
        }
    }

    FARMING_ACTIONS = {
        'IRRIGATE': {
            'en': 'Irrigation needed',
            'hi': 'सिंचाई करें',
            'hr': 'पानी देना जरूरी है'
        },
        'SPRAY': {
            'en': 'Suitable for spraying',
            'hi': 'छिड़काव के लिए उपयुक्त',
            'hr': 'दवाई डालने का टैम है'
        },
        'PROTECT': {
            'en': 'Protect crops',
            'hi': 'फसल की रक्षा करें',
            'hr': 'फसल की रखवाली करें'
        },
        'HARVEST': {
            'en': 'Good for harvesting',
            'hi': 'कटाई के लिए उपयुक्त',
            'hr': 'कटाई का बढ़िया टैम है'
        }
    }

    def __init__(self, preferred_language: str = None):
        """
        Initialize translator with preferred language.
        
        Args:
            preferred_language: Language code ('en', 'hi', 'hr')
        """
        self.language = preferred_language or WEATHER_CONFIG['DEFAULT_LANGUAGE']
        if self.language not in WEATHER_CONFIG['LANGUAGES']:
            self.language = 'en'

    def get_weather_condition(self, condition: str) -> str:
        """Get weather condition in preferred language."""
        try:
            return WEATHER_CONDITIONS[condition][self.language]
        except KeyError:
            return condition

    def get_temperature_description(self, temperature: float) -> str:
        """Get temperature description in preferred language."""
        if temperature <= 5:
            range_key = 'VERY_COLD'
        elif temperature <= 15:
            range_key = 'COLD'
        elif temperature <= 25:
            range_key = 'MODERATE'
        elif temperature <= 35:
            range_key = 'WARM'
        else:
            range_key = 'HOT'
        
        return self.TEMPERATURE_RANGES[range_key][self.language]

    def get_soil_condition(self, moisture_percentage: float) -> str:
        """Get soil condition description in preferred language."""
        if moisture_percentage < 30:
            condition = 'DRY'
        elif moisture_percentage > 70:
            condition = 'WET'
        else:
            condition = 'MOIST'
        
        return self.SOIL_CONDITIONS[condition][self.language]

    def get_alert_type(self, alert_type: str) -> str:
        """Get alert type in preferred language."""
        try:
            return self.ALERT_TYPES[alert_type][self.language]
        except KeyError:
            return alert_type

    def get_farming_action(self, action: str) -> str:
        """Get farming action in preferred language."""
        try:
            return self.FARMING_ACTIONS[action][self.language]
        except KeyError:
            return action

    def translate_weather_data(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate weather data dictionary to preferred language.
        
        Args:
            weather_data: Weather data dictionary
            
        Returns:
            Dictionary with translated values
        """
        translated = weather_data.copy()
        
        if 'weather_condition' in translated:
            translated['weather_condition'] = self.get_weather_condition(
                translated['weather_condition']
            )
        
        if 'temperature' in translated:
            translated['temperature_description'] = self.get_temperature_description(
                translated['temperature']
            )
        
        if 'soil_moisture' in translated:
            translated['soil_condition'] = self.get_soil_condition(
                translated['soil_moisture']
            )
        
        return translated

    def translate_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate weather alert to preferred language.
        
        Args:
            alert_data: Alert data dictionary
            
        Returns:
            Dictionary with translated values
        """
        translated = alert_data.copy()
        
        if 'alert_type' in translated:
            translated['alert_type'] = self.get_alert_type(
                translated['alert_type']
            )
        
        # Add basic translated description if not provided
        if 'description' not in translated:
            translated['description'] = self.get_alert_type(
                translated['alert_type']
            )
        
        return translated

    def get_recommendations(
        self,
        weather_data: Dict[str, Any],
        crop_type: Optional[str] = None
    ) -> List[str]:
        """
        Get weather-based farming recommendations in preferred language.
        
        Args:
            weather_data: Weather data dictionary
            crop_type: Optional crop type for specific recommendations
            
        Returns:
            List of translated recommendations
        """
        recommendations = []
        
        # Irrigation recommendations
        if weather_data.get('soil_moisture', 0) < 30:
            recommendations.append(self.get_farming_action('IRRIGATE'))
        
        # Spraying conditions
        if (weather_data.get('wind_speed', 0) < 15 and 
            not weather_data.get('rainfall', 0)):
            recommendations.append(self.get_farming_action('SPRAY'))
        
        # Protection recommendations
        if weather_data.get('temperature', 20) <= 5:
            recommendations.append(self.get_farming_action('PROTECT'))
        
        return recommendations