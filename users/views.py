from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import FarmerProfile, FarmLot, Query
from .serializers import (
    FarmerProfileSerializer,
    FarmLotSerializer,
    QuerySerializer,
    FarmerRegistrationSerializer
)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = FarmerRegistrationSerializer

    @action(detail=False, methods=['post'])
    def register_farmer(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'status': 'success',
                'message': 'Farmer registered successfully',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FarmerProfileViewSet(viewsets.ModelViewSet):
    queryset = FarmerProfile.objects.all()
    serializer_class = FarmerProfileSerializer

class FarmLotViewSet(viewsets.ModelViewSet):
    queryset = FarmLot.objects.all()
    serializer_class = FarmLotSerializer

    def get_queryset(self):
        return FarmLot.objects.filter(farmer__user=self.request.user)

class QueryViewSet(viewsets.ModelViewSet):
    queryset = Query.objects.all()
    serializer_class = QuerySerializer

    def get_queryset(self):
        return Query.objects.filter(farmer__user=self.request.user)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        query = self.get_object()
        query.resolved = True
        query.resolution = request.data.get('resolution', '')
        query.save()
        return Response({
            'status': 'success',
            'message': 'Query resolved successfully'
        })
