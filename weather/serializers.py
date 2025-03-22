from rest_framework import serializers
from .models import Location, WeatherData, WeatherForecast, WeatherAlert
from .language_utils import WeatherTranslator

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'district', 'state', 'latitude', 'longitude', 'elevation']

    def to_representation(self, instance):
        """Add language context to the representation."""
        representation = super().to_representation(instance)
        representation['language'] = self.context.get('language', 'en')
        return representation

class WeatherDataSerializer(serializers.ModelSerializer):
    location_details = LocationSerializer(source='location', read_only=True)
    localized_weather_condition = serializers.SerializerMethodField()
    localized_agricultural_metrics = serializers.SerializerMethodField()

    class Meta:
        model = WeatherData
        fields = [
            'id', 'location', 'location_details', 'temperature', 'humidity',
            'rainfall', 'wind_speed', 'wind_direction', 'soil_temperature',
            'soil_moisture', 'solar_radiation', 'weather_condition', 'localized_weather_condition',
            'timestamp', 'created_at', 'data_source', 'localized_agricultural_metrics'
        ]

    def get_localized_weather_condition(self, obj):
        translator = WeatherTranslator(self.context.get('language'))
        return translator.get_weather_condition(obj.weather_condition)

    def get_localized_agricultural_metrics(self, obj):
        translator = WeatherTranslator(self.context.get('language'))
        metrics = {
            'frost_risk': obj.temperature <= 2,
            'heat_stress_risk': obj.temperature >= 35,
            'disease_favorable': obj.humidity >= 80 and obj.temperature >= 20,
            'soil_condition': translator.get_soil_condition(obj.soil_moisture) if obj.soil_moisture else None
        }
        return metrics

class WeatherForecastSerializer(serializers.ModelSerializer):
    location_details = LocationSerializer(source='location', read_only=True)
    localized_weather_condition = serializers.SerializerMethodField()
    localized_agricultural_conditions = serializers.SerializerMethodField()

    class Meta:
        model = WeatherForecast
        fields = [
            'id', 'location', 'location_details', 'forecast_date',
            'min_temperature', 'max_temperature', 'humidity',
            'rainfall_probability', 'expected_rainfall', 'wind_speed',
            'weather_condition', 'localized_weather_condition', 'frost_risk', 'heat_stress_risk',
            'created_at', 'confidence_level', 'localized_agricultural_conditions'
        ]

    def get_localized_weather_condition(self, obj):
        translator = WeatherTranslator(self.context.get('language'))
        return translator.get_weather_condition(obj.weather_condition)

    def get_localized_agricultural_conditions(self, obj):
        translator = WeatherTranslator(self.context.get('language'))
        avg_temp = (obj.max_temperature + obj.min_temperature) / 2
        return {
            'growing_conditions': (
                'favorable' if (15 <= avg_temp <= 30 and 40 <= obj.humidity <= 70)
                else 'unfavorable'
            ),
            'risks': {
                'frost': obj.min_temperature <= 2,
                'heat_stress': obj.max_temperature >= 35,
                'disease': obj.humidity >= 80 and avg_temp >= 20
            },
            'irrigation_recommendation': (
                translator.get_farming_action('IRRIGATE') if obj.rainfall_probability < 30 else
                translator.get_farming_action('SPRAY') if obj.rainfall_probability > 70 else
                'monitor'
            )
        }

class WeatherAlertSerializer(serializers.ModelSerializer):
    location_details = LocationSerializer(source='location', read_only=True)
    affected_crops = serializers.StringRelatedField(many=True, read_only=True)
    localized_alert_type = serializers.SerializerMethodField()
    localized_description = serializers.SerializerMethodField()
    localized_recommended_actions = serializers.SerializerMethodField()

    class Meta:
        model = WeatherAlert
        fields = [
            'id', 'location', 'location_details', 'alert_type', 'localized_alert_type',
            'severity', 'description', 'localized_description', 'recommended_actions', 'localized_recommended_actions',
            'start_time', 'end_time', 'created_at', 'is_active', 'affected_crops',
            'resolution_notes', 'actual_impact', 'resolved_at'
        ]

    def get_localized_alert_type(self, obj):
        translator = WeatherTranslator(self.context.get('language'))
        return translator.get_alert_type(obj.alert_type)

    def get_localized_description(self, obj):
        translator = WeatherTranslator(self.context.get('language'))
        return translator.get_alert_type(obj.description)

    def get_localized_recommended_actions(self, obj):
        translator = WeatherTranslator(self.context.get('language'))
        return translator.get_farming_action(obj.recommended_actions)

class LocationWeatherSerializer(serializers.Serializer):
    location = LocationSerializer()
    current_weather = WeatherDataSerializer()
    historical_context = serializers.DictField()
    agricultural_summary = serializers.DictField()
    forecasts = WeatherForecastSerializer(many=True)
    active_alerts = WeatherAlertSerializer(many=True)

    def to_representation(self, instance):
        """Add language context to the representation."""
        representation = super().to_representation(instance)
        representation['language'] = self.context.get('language', 'en')
        return representation

class WeatherStatsSerializer(serializers.Serializer):
    location = LocationSerializer()
    date = serializers.DateField()
    temperature_stats = serializers.DictField(
        child=serializers.FloatField(),
        default={'avg': None, 'min': None, 'max': None}
    )
    rainfall_stats = serializers.DictField(
        child=serializers.FloatField(),
        default={'total': None, 'days_with_rain': None}
    )
    humidity_stats = serializers.DictField(
        child=serializers.FloatField(),
        default={'avg': None, 'min': None, 'max': None}
    )
    soil_conditions = serializers.DictField(
        child=serializers.FloatField(),
        default={'avg_moisture': None, 'avg_temperature': None}
    )
    alerts_summary = serializers.DictField(
        child=serializers.IntegerField(),
        default={'total': 0, 'high_severity': 0}
    )
    agricultural_metrics = serializers.DictField(
        child=serializers.IntegerField(),
        default={
            'frost_days': 0,
            'heat_stress_days': 0,
            'disease_risk_days': 0,
            'optimal_growing_days': 0
        }
    )

    def to_representation(self, instance):
        """Add language context to the representation."""
        representation = super().to_representation(instance)
        representation['language'] = self.context.get('language', 'en')
        return representation

class HistoricalWeatherSerializer(serializers.Serializer):
    date_range = serializers.DictField(
        child=serializers.DateField(),
        default={'start': None, 'end': None}
    )
    daily_data = WeatherStatsSerializer(many=True)
    period_summary = serializers.DictField()
    trends = serializers.DictField()

    def to_representation(self, instance):
        """Add language context to the representation."""
        representation = super().to_representation(instance)
        representation['language'] = self.context.get('language', 'en')
        return representation
