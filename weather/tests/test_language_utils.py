"""
Tests for language utility functions.
"""

from django.test import TestCase
from ..language_utils import WeatherTranslator

class WeatherTranslatorTests(TestCase):
    def setUp(self):
        self.translator_en = WeatherTranslator('en')
        self.translator_hi = WeatherTranslator('hi')
        self.translator_hr = WeatherTranslator('hr')

    def test_get_weather_condition(self):
        """Test weather condition translation."""
        self.assertEqual(
            self.translator_en.get_weather_condition('CLEAR'),
            'Clear'
        )
        self.assertEqual(
            self.translator_hi.get_weather_condition('CLEAR'),
            'साफ़'
        )
        self.assertEqual(
            self.translator_hr.get_weather_condition('CLEAR'),
            'साफ'
        )

    def test_get_temperature_description(self):
        """Test temperature description translation."""
        self.assertEqual(
            self.translator_en.get_temperature_description(10),
            'Cold'
        )
        self.assertEqual(
            self.translator_hi.get_temperature_description(10),
            'ठंडा'
        )
        self.assertEqual(
            self.translator_hr.get_temperature_description(10),
            'ठंडा'
        )

    def test_get_soil_condition(self):
        """Test soil condition translation."""
        self.assertEqual(
            self.translator_en.get_soil_condition(20),
            'Dry soil - irrigation needed'
        )
        self.assertEqual(
            self.translator_hi.get_soil_condition(20),
            'सूखी मिट्टी - सिंचाई की आवश्यकता है'
        )
        self.assertEqual(
            self.translator_hr.get_soil_condition(20),
            'सूखी माटी - पानी की जरूरत है'
        )

    def test_get_alert_type(self):
        """Test alert type translation."""
        self.assertEqual(
            self.translator_en.get_alert_type('FROST'),
            'Frost Warning'
        )
        self.assertEqual(
            self.translator_hi.get_alert_type('FROST'),
            'पाला चेतावनी'
        )
        self.assertEqual(
            self.translator_hr.get_alert_type('FROST'),
            'पाला की चेतावनी'
        )

    def test_get_farming_action(self):
        """Test farming action translation."""
        self.assertEqual(
            self.translator_en.get_farming_action('IRRIGATE'),
            'Irrigation needed'
        )
        self.assertEqual(
            self.translator_hi.get_farming_action('IRRIGATE'),
            'सिंचाई करें'
        )
        self.assertEqual(
            self.translator_hr.get_farming_action('IRRIGATE'),
            'पानी देना जरूरी है'
        )

    def test_translate_weather_data(self):
        """Test weather data translation."""
        weather_data = {
            'temperature': 10,
            'humidity': 50,
            'weather_condition': 'CLEAR',
            'soil_moisture': 20
        }
        translated_data = self.translator_hi.translate_weather_data(weather_data)
        
        self.assertEqual(translated_data['weather_condition'], 'साफ़')
        self.assertEqual(translated_data['temperature_description'], 'ठंडा')
        self.assertEqual(translated_data['soil_condition'], 'सूखी मिट्टी - सिंचाई की आवश्यकता है')

    def test_translate_alert(self):
        """Test alert translation."""
        alert_data = {
            'alert_type': 'FROST',
            'description': 'Test alert'
        }
        translated_data = self.translator_hr.translate_alert(alert_data)
        
        self.assertEqual(translated_data['alert_type'], 'पाला की चेतावनी')
        self.assertEqual(translated_data['description'], 'Test alert')

    def test_get_recommendations(self):
        """Test farming recommendations translation."""
        weather_data = {
            'temperature': 10,
            'humidity': 50,
            'wind_speed': 10,
            'rainfall': 0,
            'soil_moisture': 20
        }
        recommendations = self.translator_hi.get_recommendations(weather_data)
        
        self.assertIn('सिंचाई करें', recommendations)
        self.assertIn('छिड़काव के लिए उपयुक्त', recommendations)
        self.assertIn('फसल की रक्षा करें', recommendations)