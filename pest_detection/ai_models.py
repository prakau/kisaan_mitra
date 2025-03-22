from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

@lru_cache(maxsize=1)
def get_classifier():
    from transformers import (
        pipeline,
        AutoImageProcessor,
        AutoModelForImageClassification
    )
    import torch
    from pathlib import Path
    import requests
    from PIL import Image
    from io import BytesIO

    class PlantDiseaseDetector:
        def __init__(self):
            self.model_name = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
            # Initialize both pipeline and direct model loading for flexibility
            self.pipeline = pipeline("image-classification", model=self.model_name)
            self.processor = AutoImageProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForImageClassification.from_pretrained(self.model_name)
            
            if torch.cuda.is_available():
                self.model = self.model.to('cuda')

        def load_image(self, image_url):
            """Load an image from URL or local path"""
            if image_url.startswith(('http://', 'https://')):
                response = requests.get(image_url)
                image = Image.open(BytesIO(response.content))
            else:
                image = Image.open(image_url)
            return image

        def predict_pipeline(self, image_url):
            """Use the pipeline approach for prediction"""
            image = self.load_image(image_url)
            results = self.pipeline(image)
            return results

        def predict_direct(self, image_url):
            """Use direct model approach for more control over the prediction process"""
            image = self.load_image(image_url)
            inputs = self.processor(images=image, return_tensors="pt")
            
            if torch.cuda.is_available():
                inputs = {k: v.to('cuda') for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            predicted_class_idx = logits.argmax(-1).item()
            predicted_class = self.model.config.id2label[predicted_class_idx]
            confidence = torch.softmax(logits, dim=-1)[0][predicted_class_idx].item()

            return {
                'label': predicted_class,
                'confidence': confidence
            }

    class PlantDiseaseClassifier:
        def __init__(self):
            # Initialize disease detector
            self.detector = PlantDiseaseDetector()

        def classify_image(self, image_url):
            """
            Classify plant disease from image and return structured response
            """
            try:
                # Use direct prediction for more control
                result = self.detector.predict_direct(image_url)
                
                # Parse the disease label
                disease_label = result['label']
                confidence = result['confidence']

                # Structure the response
                response = {
                    'success': True,
                    'disease_detected': disease_label != 'healthy',
                    'classification': disease_label,
                    'confidence_score': confidence,
                    'recommendation': self._get_recommendation(disease_label)
                }

            except Exception as e:
                response = {
                    'success': False,
                    'error': str(e)
                }

            return response

        def _get_recommendation(self, disease_label):
            """
            Generate basic recommendations based on disease classification
            """
            if disease_label == 'healthy':
                return "Plant appears healthy. Continue regular maintenance."
            else:
                return (
                    f"Disease detected: {disease_label}. "
                    "Please consult with local agricultural experts for specific treatment. "
                    "Consider isolating affected plants to prevent spread."
                )

    return PlantDiseaseClassifier()

# Global instance with lazy loading
_classifier = None

def get_plant_disease_classifier():
    global _classifier
    if _classifier is None:
        _classifier = get_classifier()
    return _classifier
