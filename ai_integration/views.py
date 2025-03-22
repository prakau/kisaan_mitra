from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from transformers import pipeline

class CropClassificationViewSet(viewsets.ViewSet):
    parser_classes = (MultiPartParser, FormParser)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize the crop classification pipeline using a Hugging Face model
        self.classifier = pipeline("image-classification", 
                                 model="iammartian0/vegetation_classification_model")

    def create(self, request):
        image = request.FILES.get("image")
        if not image:
            return Response(
                {"error": "No image provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Process the image using the Hugging Face model
            result = self.classifier(image)
            
            # Format the response
            response_data = {
                'predictions': [
                    {
                        'label': pred['label'],
                        'confidence': f"{pred['score']:.2%}"
                    }
                    for pred in result
                ]
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request):
        return Response({
            "message": "Send a POST request with an image file to classify crops."
        })
