"""
Offline data manager for weather module.
Handles data synchronization, storage, and offline access capabilities.
"""

import json
import logging
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings

from .models import WeatherData, WeatherForecast, WeatherAlert
from .exceptions import WeatherDataError
from .config import WEATHER_CONFIG

logger = logging.getLogger(__name__)

class OfflineDataManager:
    """
    Manages offline data storage and synchronization for the weather module.
    Provides mechanisms to store and retrieve weather data when offline.
    """

    def __init__(self):
        self.offline_db_path = Path(settings.BASE_DIR) / 'weather_offline.db'
        self.sync_interval = WEATHER_CONFIG['OFFLINE_MODE']['SYNC_FREQUENCY']
        self.min_storage_days = WEATHER_CONFIG['OFFLINE_MODE']['MIN_STORAGE_DAYS']
        self.compress_data = WEATHER_CONFIG['OFFLINE_MODE']['COMPRESS_DATA']
        
    def initialize_offline_storage(self) -> None:
        """Initialize SQLite database for offline storage."""
        try:
            conn = sqlite3.connect(str(self.offline_db_path))
            cursor = conn.cursor()

            # Create tables for offline storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    rainfall REAL,
                    timestamp TEXT,
                    data_source TEXT,
                    sync_status TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER NOT NULL,
                    forecast_date TEXT,
                    min_temperature REAL,
                    max_temperature REAL,
                    humidity REAL,
                    sync_status TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER NOT NULL,
                    alert_type TEXT,
                    severity TEXT,
                    description TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    sync_status TEXT
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Offline storage initialized successfully")
        
        except sqlite3.Error as e:
            logger.error(f"Error initializing offline storage: {e}")
            raise WeatherDataError("Failed to initialize offline storage")

    def sync_data(self, location_id: int) -> bool:
        """
        Synchronize offline data with server when connection is available.
        
        Args:
            location_id: ID of the location to sync data for
            
        Returns:
            bool: True if sync was successful
        """
        try:
            # Check if sync is needed
            last_sync = cache.get(f'weather_last_sync_{location_id}')
            if last_sync and (timezone.now() - last_sync).hours < self.sync_interval:
                return True

            conn = sqlite3.connect(str(self.offline_db_path))
            cursor = conn.cursor()

            # Sync unsynced weather data
            cursor.execute(
                "SELECT * FROM weather_data WHERE sync_status = 'pending'"
            )
            pending_data = cursor.fetchall()
            
            for data in pending_data:
                weather_data = WeatherData(
                    location_id=data[1],
                    temperature=data[2],
                    humidity=data[3],
                    rainfall=data[4],
                    timestamp=datetime.fromisoformat(data[5]),
                    data_source=data[6]
                )
                weather_data.save()
                
                cursor.execute(
                    "UPDATE weather_data SET sync_status = 'synced' WHERE id = ?",
                    (data[0],)
                )

            # Sync alerts
            cursor.execute(
                "SELECT * FROM weather_alerts WHERE sync_status = 'pending'"
            )
            pending_alerts = cursor.fetchall()
            
            for alert in pending_alerts:
                weather_alert = WeatherAlert(
                    location_id=alert[1],
                    alert_type=alert[2],
                    severity=alert[3],
                    description=alert[4],
                    start_time=datetime.fromisoformat(alert[5]),
                    end_time=datetime.fromisoformat(alert[6])
                )
                weather_alert.save()
                
                cursor.execute(
                    "UPDATE weather_alerts SET sync_status = 'synced' WHERE id = ?",
                    (alert[0],)
                )

            conn.commit()
            conn.close()

            # Update last sync time
            cache.set(
                f'weather_last_sync_{location_id}',
                timezone.now(),
                timeout=self.sync_interval * 3600
            )
            
            logger.info(f"Data sync completed for location {location_id}")
            return True

        except (sqlite3.Error, Exception) as e:
            logger.error(f"Error syncing data: {e}")
            return False

    def store_offline_data(
        self,
        location_id: int,
        data_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Store weather data locally for offline access.
        
        Args:
            location_id: Location ID
            data_type: Type of data (weather_data, forecast, alert)
            data: Data to store
            
        Returns:
            bool: True if storage was successful
        """
        try:
            conn = sqlite3.connect(str(self.offline_db_path))
            cursor = conn.cursor()

            if data_type == 'weather_data':
                cursor.execute("""
                    INSERT INTO weather_data 
                    (location_id, temperature, humidity, rainfall, 
                     timestamp, data_source, sync_status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """, (
                    location_id,
                    data['temperature'],
                    data['humidity'],
                    data['rainfall'],
                    data['timestamp'].isoformat(),
                    data['data_source']
                ))
            
            elif data_type == 'alert':
                cursor.execute("""
                    INSERT INTO weather_alerts
                    (location_id, alert_type, severity, description,
                     start_time, end_time, sync_status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """, (
                    location_id,
                    data['alert_type'],
                    data['severity'],
                    data['description'],
                    data['start_time'].isoformat(),
                    data['end_time'].isoformat()
                ))

            conn.commit()
            conn.close()
            return True

        except sqlite3.Error as e:
            logger.error(f"Error storing offline data: {e}")
            return False

    def get_offline_data(
        self,
        location_id: int,
        data_type: str,
        start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve stored offline data.
        
        Args:
            location_id: Location ID
            data_type: Type of data to retrieve
            start_date: Optional start date for data retrieval
            
        Returns:
            List of data dictionaries
        """
        try:
            conn = sqlite3.connect(str(self.offline_db_path))
            cursor = conn.cursor()

            if data_type == 'weather_data':
                query = """
                    SELECT * FROM weather_data 
                    WHERE location_id = ?
                """
                if start_date:
                    query += " AND timestamp >= ?"
                    cursor.execute(query, (location_id, start_date.isoformat()))
                else:
                    cursor.execute(query, (location_id,))
                
                columns = ['id', 'location_id', 'temperature', 'humidity',
                          'rainfall', 'timestamp', 'data_source', 'sync_status']
                
            elif data_type == 'alerts':
                query = """
                    SELECT * FROM weather_alerts 
                    WHERE location_id = ?
                """
                if start_date:
                    query += " AND start_time >= ?"
                    cursor.execute(query, (location_id, start_date.isoformat()))
                else:
                    cursor.execute(query, (location_id,))
                
                columns = ['id', 'location_id', 'alert_type', 'severity',
                          'description', 'start_time', 'end_time', 'sync_status']

            results = cursor.fetchall()
            conn.close()

            return [dict(zip(columns, row)) for row in results]

        except sqlite3.Error as e:
            logger.error(f"Error retrieving offline data: {e}")
            return []

    def cleanup_old_data(self) -> None:
        """Remove old data from offline storage."""
        try:
            cutoff_date = (
                timezone.now() - timedelta(days=self.min_storage_days)
            ).isoformat()
            
            conn = sqlite3.connect(str(self.offline_db_path))
            cursor = conn.cursor()

            # Clean up old weather data
            cursor.execute(
                "DELETE FROM weather_data WHERE timestamp < ? AND sync_status = 'synced'",
                (cutoff_date,)
            )

            # Clean up old alerts
            cursor.execute(
                "DELETE FROM weather_alerts WHERE end_time < ? AND sync_status = 'synced'",
                (cutoff_date,)
            )

            conn.commit()
            conn.close()
            logger.info("Old data cleanup completed")

        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old data: {e}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about offline storage usage."""
        try:
            conn = sqlite3.connect(str(self.offline_db_path))
            cursor = conn.cursor()

            stats = {
                'weather_data_count': cursor.execute(
                    "SELECT COUNT(*) FROM weather_data"
                ).fetchone()[0],
                'alerts_count': cursor.execute(
                    "SELECT COUNT(*) FROM weather_alerts"
                ).fetchone()[0],
                'pending_sync_count': cursor.execute(
                    "SELECT COUNT(*) FROM weather_data WHERE sync_status = 'pending'"
                ).fetchone()[0],
                'storage_size_kb': Path(self.offline_db_path).stat().st_size / 1024
            }

            conn.close()
            return stats

        except sqlite3.Error as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}