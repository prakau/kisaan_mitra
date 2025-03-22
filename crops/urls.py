from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'crops', views.CropViewSet)
router.register(r'recommendations', views.CropRecommendationViewSet)
router.register(r'planting-schedules', views.PlantingScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
