from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CropClassificationViewSet

router = DefaultRouter()
router.register(r'crop-classification', CropClassificationViewSet, basename='crop-classification')

urlpatterns = [
    path('', include(router.urls)),
]
