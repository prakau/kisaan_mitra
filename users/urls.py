from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.FarmerProfileViewSet)
router.register(r'farm-lots', views.FarmLotViewSet)
router.register(r'queries', views.QueryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
