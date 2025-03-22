from rest_framework import serializers
from .models import ChatHistory

class ChatHistorySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = ChatHistory
        fields = ['id', 'user', 'username', 'message', 'response', 'language', 'created_at']
        read_only_fields = ['user', 'username', 'response', 'created_at']

    def get_username(self, obj):
        return obj.user.username if obj.user else None

    def create(self, validated_data):
        # Set the user from the context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
