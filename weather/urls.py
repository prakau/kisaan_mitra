from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'locations', views.LocationViewSet)
router.register(r'weather-data', views.WeatherDataViewSet)
router.register(r'forecasts', views.WeatherForecastViewSet)
router.register(r'alerts', views.WeatherAlertViewSet)
router.register(r'location-weather', views.LocationWeatherViewSet, basename='location-weather')

urlpatterns = [
    path('', include(router.urls)),
]
