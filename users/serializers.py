from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FarmerProfile, FarmLot, Query

User = get_user_model()

class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = ['id', 'user', 'phone_number', 'district', 'village', 'preferred_language']
        read_only_fields = ['user']

class FarmLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmLot
        fields = ['id', 'farmer', 'area', 'soil_type', 'location', 'current_crop']
        read_only_fields = ['farmer']

class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = ['id', 'farmer', 'subject', 'description', 'created_at', 'resolved', 'resolution']
        read_only_fields = ['farmer', 'created_at', 'resolved', 'resolution']

class FarmerRegistrationSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=15, write_only=True)
    district = serializers.CharField(max_length=100, write_only=True)
    village = serializers.CharField(max_length=100, write_only=True)
    preferred_language = serializers.ChoiceField(choices=FarmerProfile.LANGUAGE_CHOICES, write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name',
                 'phone_number', 'district', 'village', 'preferred_language']

    def create(self, validated_data):
        profile_data = {
            'phone_number': validated_data.pop('phone_number'),
            'district': validated_data.pop('district'),
            'village': validated_data.pop('village'),
            'preferred_language': validated_data.pop('preferred_language'),
        }

        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        FarmerProfile.objects.create(user=user, **profile_data)
        return user
