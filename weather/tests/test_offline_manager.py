"""
Tests for offline data management functionality.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache

from ..models import Location, WeatherData, WeatherAlert
from ..offline_manager import OfflineDataManager
from ..exceptions import WeatherDataError
from . import TEST_LOCATION_DATA, TEST_WEATHER_DATA

class OfflineDataManagerTests(TestCase):
    def setUp(self):
        self.manager = OfflineDataManager()
        
        # Use in-memory SQLite database for testing
        self.manager.offline_db_path = ':memory:'
        
        # Create test location
        self.location = Location.objects.create(**TEST_LOCATION_DATA)
        
        # Initialize storage
        self.manager.initialize_offline_storage()
        
        # Test data
        self.weather_data = {
            'location_id': self.location.id,
            'temperature': 25.5,
            'humidity': 65.0,
            'rainfall': 0.0,
            'timestamp': timezone.now(),
            'data_source': 'TEST'
        }
        
        self.alert_data = {
            'location_id': self.location.id,
            'alert_type': 'FROST',
            'severity': 'HIGH',
            'description': 'Test alert',
            'start_time': timezone.now(),
            'end_time': timezone.now() + timedelta(hours=6)
        }

    def tearDown(self):
        cache.clear()
        # Clean up any test files
        if os.path.exists('weather_offline.db'):
            os.remove('weather_offline.db')

    def test_initialize_storage(self):
        """Test offline storage initialization."""
        # Connect to the in-memory database
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='weather_data'
        """)
        self.assertIsNotNone(cursor.fetchone())
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='weather_alerts'
        """)
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()

    def test_store_offline_data(self):
        """Test storing weather data offline."""
        # Store weather data
        success = self.manager.store_offline_data(
            self.location.id,
            'weather_data',
            self.weather_data
        )
        self.assertTrue(success)
        
        # Verify storage
        stored_data = self.manager.get_offline_data(
            self.location.id,
            'weather_data'
        )
        self.assertEqual(len(stored_data), 1)
        self.assertEqual(
            Decimal(str(stored_data[0]['temperature'])),
            Decimal(str(self.weather_data['temperature']))
        )

    def test_store_alert_data(self):
        """Test storing alert data offline."""
        success = self.manager.store_offline_data(
            self.location.id,
            'alert',
            self.alert_data
        )
        self.assertTrue(success)
        
        # Verify storage
        stored_alerts = self.manager.get_offline_data(
            self.location.id,
            'alerts'
        )
        self.assertEqual(len(stored_alerts), 1)
        self.assertEqual(stored_alerts[0]['alert_type'], 'FROST')

    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_sync_data(self, mock_cache_set, mock_cache_get):
        """Test data synchronization."""
        mock_cache_get.return_value = None
        
        # Store some test data
        self.manager.store_offline_data(
            self.location.id,
            'weather_data',
            self.weather_data
        )
        
        # Sync data
        success = self.manager.sync_data(self.location.id)
        self.assertTrue(success)
        
        # Verify data was synced
        weather_data = WeatherData.objects.filter(location=self.location)
        self.assertEqual(weather_data.count(), 1)
        
        # Verify sync status was updated
        stored_data = self.manager.get_offline_data(
            self.location.id,
            'weather_data'
        )
        self.assertEqual(stored_data[0]['sync_status'], 'synced')

    def test_cleanup_old_data(self):
        """Test cleaning up old offline data."""
        # Store old data
        old_data = self.weather_data.copy()
        old_data['timestamp'] = timezone.now() - timedelta(days=30)
        self.manager.store_offline_data(
            self.location.id,
            'weather_data',
            old_data
        )
        
        # Store recent data
        self.manager.store_offline_data(
            self.location.id,
            'weather_data',
            self.weather_data
        )
        
        # Mark old data as synced
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE weather_data SET sync_status = 'synced' WHERE sync_status = 'pending'"
        )
        conn.commit()
        conn.close()
        
        # Run cleanup
        self.manager.cleanup_old_data()
        
        # Verify only recent data remains
        stored_data = self.manager.get_offline_data(
            self.location.id,
            'weather_data'
        )
        self.assertEqual(len(stored_data), 1)
        self.assertEqual(
            datetime.fromisoformat(stored_data[0]['timestamp']).date(),
            self.weather_data['timestamp'].date()
        )

    def test_get_storage_stats(self):
        """Test getting storage statistics."""
        # Store some test data
        self.manager.store_offline_data(
            self.location.id,
            'weather_data',
            self.weather_data
        )
        self.manager.store_offline_data(
            self.location.id,
            'alert',
            self.alert_data
        )
        
        # Get stats
        stats = self.manager.get_storage_stats()
        
        self.assertEqual(stats['weather_data_count'], 1)
        self.assertEqual(stats['alerts_count'], 1)
        self.assertEqual(stats['pending_sync_count'], 1)
        self.assertIsInstance(stats['storage_size_kb'], float)

    def test_error_handling(self):
        """Test error handling in offline operations."""
        # Test invalid data type
        with self.assertRaises(sqlite3.Error):
            self.manager.store_offline_data(
                self.location.id,
                'invalid_type',
                {}
            )
        
        # Test invalid location ID
        data = self.manager.get_offline_data(999, 'weather_data')
        self.assertEqual(len(data), 0)

    def test_date_filtering(self):
        """Test date-based filtering of offline data."""
        # Store data with different dates
        old_data = self.weather_data.copy()
        old_data['timestamp'] = timezone.now() - timedelta(days=7)
        self.manager.store_offline_data(
            self.location.id,
            'weather_data',
            old_data
        )
        
        self.manager.store_offline_data(
            self.location.id,
            'weather_data',
            self.weather_data
        )
        
        # Get data from last 3 days
        start_date = timezone.now() - timedelta(days=3)
        filtered_data = self.manager.get_offline_data(
            self.location.id,
            'weather_data',
            start_date
        )
        
        self.assertEqual(len(filtered_data), 1)
        self.assertEqual(
            datetime.fromisoformat(filtered_data[0]['timestamp']).date(),
            self.weather_data['timestamp'].date()
        )