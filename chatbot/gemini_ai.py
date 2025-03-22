from django.conf import settings
import google.generativeai as genai

class GeminiAI:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # System prompt to configure the assistant's behavior
        self.system_prompt = """You are an agricultural expert assistant for Kisaan Mitra, an app that helps farmers in Haryana, India.
            You specialize in vegetable farming and can provide advice on:
            - Crop selection and management
            - Pest and disease identification
            - Irrigation and fertilization
            - Weather-based recommendations
            - Market trends and pricing
            Please provide practical, region-specific advice in simple language."""

    def get_response(self, message, language='en'):
        try:
            # If language is not English, append translation request
            if language != 'en':
                message += f"\n(Please respond in {'Hindi' if language == 'hi' else 'Haryanvi'} language)"

            # Combine system prompt with user message
            full_prompt = f"{self.system_prompt}\n\nUser Query: {message}"

            # Get response from Gemini
            response = self.model.generate_content(full_prompt)
            
            return {
                'status': 'success',
                'message': response.text,
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
            }

    def get_crop_recommendation(self, soil_type, season, district):
        prompt = f"""As an agricultural expert, recommend suitable vegetable crops for:
        Soil Type: {soil_type}
        Season: {season}
        District: {district}, Haryana
        
        Please provide:
        1. Top 3 recommended crops
        2. Brief explanation why they are suitable
        3. Basic growing requirements
        """
        return self.get_response(prompt)

    def analyze_pest_problem(self, crop_name, symptoms, image_description=None):
        prompt = f"""Analyze this pest/disease problem for:
        Crop: {crop_name}
        Symptoms: {symptoms}
        Image Description: {image_description if image_description else 'No image provided'}
        
        Please provide:
        1. Possible identification of the problem
        2. Recommended treatment options (preferably organic)
        3. Preventive measures for the future
        """
        return self.get_response(prompt)

    def get_weather_advisory(self, crop_name, weather_data):
        prompt = f"""Based on the weather forecast:
        {weather_data}
        
        Provide farming advisory for {crop_name} including:
        1. Required precautions
        2. Irrigation adjustments if needed
        3. Any other relevant recommendations
        """
        return self.get_response(prompt)

# Initialize the Gemini AI instance
gemini_ai = GeminiAI()
