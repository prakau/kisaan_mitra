from django.contrib import admin
from .models import WeatherData, WeatherForecast, WeatherAlert

@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['location', 'temperature', 'humidity', 'rainfall',
                   'wind_speed', 'weather_condition', 'timestamp']
    search_fields = ['location']
    list_filter = ['location', 'weather_condition', 'timestamp']
    date_hierarchy = 'timestamp'

@admin.register(WeatherForecast)
class WeatherForecastAdmin(admin.ModelAdmin):
    list_display = ['location', 'forecast_date', 'min_temperature',
                   'max_temperature', 'weather_condition']
    search_fields = ['location']
    list_filter = ['location', 'weather_condition', 'forecast_date']
    date_hierarchy = 'forecast_date'

@admin.register(WeatherAlert)
class WeatherAlertAdmin(admin.ModelAdmin):
    list_display = ['location', 'alert_type', 'severity', 'start_time',
                   'end_time', 'is_active']
    search_fields = ['location', 'alert_type']
    list_filter = ['location', 'alert_type', 'severity', 'is_active']
    date_hierarchy = 'start_time'
    list_editable = ['is_active']
