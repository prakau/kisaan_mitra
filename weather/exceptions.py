"""
Custom exceptions for the weather module.
These exceptions provide more specific error handling for weather-related operations.
"""

class WeatherDataError(Exception):
    """Base exception for weather module errors."""
    pass

class InvalidLocationError(WeatherDataError):
    """Raised when a location is invalid or not found."""
    pass

class WeatherDataValidationError(WeatherDataError):
    """Raised when weather data fails validation."""
    pass

class InvalidDateRangeError(WeatherDataError):
    """Raised when a date range is invalid."""
    pass

class WeatherServiceError(WeatherDataError):
    """Raised when there's an error with external weather services."""
    pass