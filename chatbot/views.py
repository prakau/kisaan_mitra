from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ChatHistory
from .serializers import ChatHistorySerializer
from .gemini_ai import gemini_ai

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatHistory.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def send_message(self, request):
        message = request.data.get('message')
        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user's preferred language from their profile
        language = 'en'  # default to English
        if hasattr(request.user, 'farmerprofile'):
            language = request.user.farmerprofile.preferred_language

        # Get response from Gemini AI
        response = gemini_ai.get_response(message, language)

        if response['status'] == 'success':
            # Save the chat history
            chat_history = ChatHistory.objects.create(
                user=request.user,
                message=message,
                response=response['message'],
                language=language
            )
            
            return Response({
                'status': 'success',
                'message': response['message'],
                'chat_id': chat_history.id
            })
        else:
            return Response({
                'status': 'error',
                'message': response['message']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def get_crop_recommendation(self, request):
        soil_type = request.data.get('soil_type')
        season = request.data.get('season')
        district = request.data.get('district')

        if not all([soil_type, season, district]):
            return Response({
                'error': 'soil_type, season, and district are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        response = gemini_ai.get_crop_recommendation(soil_type, season, district)
        return Response(response)

    @action(detail=False, methods=['post'])
    def analyze_pest_problem(self, request):
        crop_name = request.data.get('crop_name')
        symptoms = request.data.get('symptoms')
        image_description = request.data.get('image_description')

        if not all([crop_name, symptoms]):
            return Response({
                'error': 'crop_name and symptoms are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        response = gemini_ai.analyze_pest_problem(crop_name, symptoms, image_description)
        return Response(response)

    @action(detail=False, methods=['post'])
    def get_weather_advisory(self, request):
        crop_name = request.data.get('crop_name')
        weather_data = request.data.get('weather_data')

        if not all([crop_name, weather_data]):
            return Response({
                'error': 'crop_name and weather_data are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        response = gemini_ai.get_weather_advisory(crop_name, weather_data)
        return Response(response)
