"""
Enhanced configuration settings for weather module with focus on agricultural insights
and offline capabilities for Haryana's farmers.
"""

from django.conf import settings
from typing import Dict, Any

WEATHER_CONFIG: Dict[str, Any] = {
    # Cache settings with enhanced offline support
    'CACHE_TIMEOUT': getattr(settings, 'WEATHER_CACHE_TIMEOUT', 300),
    'CACHE_KEY_PREFIX': 'weather_',
    'OFFLINE_CACHE_DAYS': 7,  # Days of data to cache for offline access

    # Forecast settings tailored for Haryana
    'MAX_FORECAST_DAYS': getattr(settings, 'WEATHER_MAX_FORECAST_DAYS', 7),
    'DEFAULT_RADIUS_KM': getattr(settings, 'WEATHER_DEFAULT_RADIUS_KM', 10),
    'LOCAL_WEATHER_STATIONS': getattr(settings, 'WEATHER_LOCAL_STATIONS', []),

    # Agricultural alert thresholds specific to Haryana vegetables
    'ALERT_THRESHOLDS': {
        'HIGH_TEMPERATURE': getattr(settings, 'WEATHER_HIGH_TEMP_THRESHOLD', 35),
        'LOW_TEMPERATURE': getattr(settings, 'WEATHER_LOW_TEMP_THRESHOLD', 2),
        'HIGH_HUMIDITY': getattr(settings, 'WEATHER_HIGH_HUMIDITY_THRESHOLD', 80),
        'LOW_SOIL_MOISTURE': getattr(settings, 'WEATHER_LOW_SOIL_MOISTURE_THRESHOLD', 30),
        'HIGH_SOIL_MOISTURE': getattr(settings, 'WEATHER_HIGH_SOIL_MOISTURE_THRESHOLD', 70),
        'FROST_WARNING_TEMP': 4,  # Temperature threshold for frost warnings
        'HEATWAVE_WARNING_TEMP': 40  # Temperature threshold for heatwave warnings
    },

    # Growing Degree Days calculation
    'GROWING_DEGREE_DAYS': {
        'BASE_TEMPERATURE': getattr(settings, 'WEATHER_GDD_BASE_TEMP', 10),
        'CROP_SPECIFIC_BASE_TEMPS': {
            'TOMATO': 10,
            'POTATO': 7,
            'CAULIFLOWER': 5,
            'CUCUMBER': 12,
        }
    },

    # Localization settings
    'LANGUAGES': {
        'hi': 'Hindi',
        'hr': 'Haryanvi',
        'en': 'English'
    },
    'DEFAULT_LANGUAGE': 'hi',

    # Data sources with priority
    'DATA_SOURCES': {
        'PRIMARY': 'IMD',
        'SECONDARY': ['LOCAL_STATIONS', 'WEATHER_UNDERGROUND'],
        'FALLBACK': 'CACHED_DATA'
    },

    # Offline mode settings
    'OFFLINE_MODE': {
        'ENABLED': True,
        'SYNC_FREQUENCY': 6,  # Hours between sync attempts
        'MIN_STORAGE_DAYS': 3,  # Minimum days of data to store
        'COMPRESS_DATA': True,
        'PRIORITY_FEATURES': [
            'CURRENT_WEATHER',
            'BASIC_FORECAST',
            'CRITICAL_ALERTS'
        ]
    },

    # Agricultural insights configuration
    'AGRICULTURAL_INSIGHTS': {
        'ENABLED': True,
        'UPDATE_FREQUENCY': 6,  # Hours
        'IRRIGATION_CHECK_FREQUENCY': 4,  # Hours
        'CROP_STRESS_MONITORING': True,
        'DISEASE_RISK_MONITORING': True
    },

    # Notification settings
    'NOTIFICATIONS': {
        'CHANNELS': ['APP', 'SMS', 'WHATSAPP'],
        'PRIORITY_LEVELS': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
        'SMS_ENABLED': True,
        'WHATSAPP_ENABLED': True,
        'NOTIFICATION_QUIET_HOURS': {
            'START': 22,  # 10 PM
            'END': 6     # 6 AM
        }
    },

    # Integration settings
    'INTEGRATIONS': {
        'PEST_DETECTION': True,
        'CROP_ADVISORY': True,
        'MARKET_PRICES': True,
        'GOVERNMENT_SCHEMES': True
    }
}

# Weather condition categories with local language support
WEATHER_CONDITIONS = {
    'CLEAR': {
        'en': 'Clear',
        'hi': 'साफ़',
        'hr': 'साफ'
    },
    'PARTLY_CLOUDY': {
        'en': 'Partly Cloudy',
        'hi': 'आंशिक रूप से बादल',
        'hr': 'थोड़े बादल'
    },
    'CLOUDY': {
        'en': 'Cloudy',
        'hi': 'बादल',
        'hr': 'बादल'
    },
    'RAIN': {
        'en': 'Rain',
        'hi': 'बारिश',
        'hr': 'बरखा'
    },
    'THUNDERSTORM': {
        'en': 'Thunderstorm',
        'hi': 'आंधी',
        'hr': 'आंधी'
    },
    'FOG': {
        'en': 'Fog',
        'hi': 'कोहरा',
        'hr': 'कुहरा'
    },
    'HAZE': {
        'en': 'Haze',
        'hi': 'धुंध',
        'hr': 'धुंध'
    }
}

# Alert severity levels
ALERT_SEVERITY_LEVELS = {
    'LOW': 1,
    'MEDIUM': 2,
    'HIGH': 3,
    'EXTREME': 4
}

# Agricultural calendar for Haryana
AGRICULTURAL_CALENDAR = {
    'RABI': {
        'START_MONTH': 10,  # October
        'END_MONTH': 3,    # March
        'CROPS': ['POTATO', 'CAULIFLOWER', 'TOMATO']
    },
    'KHARIF': {
        'START_MONTH': 6,   # June
        'END_MONTH': 9,    # September
        'CROPS': ['CUCUMBER', 'BITTER_GOURD', 'OKRA']
    },
    'ZAID': {
        'START_MONTH': 3,   # March
        'END_MONTH': 6,    # June
        'CROPS': ['BOTTLE_GOURD', 'PUMPKIN']
    }
}

# Critical periods for weather monitoring
CRITICAL_PERIODS = {
    'SOWING': {'days_before': 7, 'days_after': 7},
    'GERMINATION': {'days_before': 3, 'days_after': 7},
    'FLOWERING': {'days_before': 5, 'days_after': 10},
    'HARVESTING': {'days_before': 7, 'days_after': 3}
}