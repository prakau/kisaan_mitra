from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pests', views.PestViewSet)
router.register(r'diseases', views.DiseaseViewSet)
router.register(r'detection-results', views.DetectionResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
