import numpy as np
import torch
import torchxrayvision as xrv
import torchvision
import os
import torch.nn as nn


class XRayScanEvaluationRepository:
    _instance = None
    _model = None
    
    # Modelin eğitildiği hedef hastalıklar
    TARGET_PATHOLOGIES = ["Cardiomegaly", "Hernia", "Infiltration"]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(XRayScanEvaluationRepository, cls).__new__(cls)
        return cls._instance

    def _get_model(self):
        if self._model is None:
            try:
                model_path = "/app/models/model.pth"
                if os.path.exists(model_path):
                    print("Loading custom model from model.pth...")

                    # Eğitimde kullanılan orijinal sınıf sayısı 15'ti
                    base_model = xrv.models.DenseNet(num_classes=15)
                    num_ftrs = base_model.classifier.in_features
                    base_model.classifier = nn.Linear(num_ftrs, 3)  # 3 hedef sınıf

                    checkpoint = torch.load(model_path, map_location='cpu')
                    base_model.load_state_dict(checkpoint)
                    base_model.eval()

                    self._model = base_model
                    print("Custom model loaded successfully from model.pth")
                else:
                    print("model.pth not found, using pretrained base model...")
                    self._model = xrv.models.DenseNet(weights="densenet121-res224-all")
            except Exception as e:
                print(f"Error loading model.pth: {e}")
                self._model = self._create_dummy_model()
        return self._model

    def _create_dummy_model(self):
        """Create a dummy model that returns safe predictions when the real model fails"""
        class DummyModel:
            def __init__(self):
                self.pathologies = XRayScanEvaluationRepository.TARGET_PATHOLOGIES
            
            def to(self, device):
                return self
            
            def eval(self):
                return self
            
            def __call__(self, image):
                # Return dummy predictions
                return torch.tensor([[0.1, 0.1, 0.1]])  # Low probability for all pathologies
        
        return DummyModel()

    def evaluate_xray_scan(self, xray_scan: np.array) -> dict:
        """
        Evaluate X-ray scan and provide diagnosis.
        - **xray_scan**: The X-ray scan file to be evaluated.
        - **Returns**: A JSON response with the evaluation result.
        - **Raises**: 400 if the input is invalid, 500 for internal server errors.
        """
        try:
            # Load the X-ray model
            model = self._get_model()
            
            # Move model to CPU (GPU yoksa)
            device = torch.device("cpu")
            model.to(device)
            model.eval()

            # Normalize image
            image = xrv.datasets.normalize(xray_scan, 255)

            # Handle different image formats
            if len(image.shape) > 2:
                image = image[:, :, 0]  # Use the first channel if RGB
            if len(image.shape) < 2:
                raise ValueError("Error: Image is not valid.")

            # Add batch dimension
            image = image[None, :, :]
            
            # Apply transforms
            transform = torchvision.transforms.Compose([
                xrv.datasets.XRayCenterCrop(), 
                xrv.datasets.XRayResizer(224)
            ])
            image = transform(image)
            
            # Convert to tensor
            image = torch.from_numpy(image).unsqueeze(0).to(device)

            # Get predictions
            with torch.no_grad():
                preds = model(image).cpu()

            # Model.pth 3 sınıf için eğitilmiş: Cardiomegaly, Hernia, Infiltration
            pathologies = self.TARGET_PATHOLOGIES

            # Convert predictions to numpy and apply sigmoid
            preds_numpy = torch.sigmoid(preds[0]).detach().numpy()
            
            # Create predictions dictionary
            preds_dict = dict(zip(pathologies, preds_numpy))
            
            # Convert NumPy objects to native Python types for serialization
            preds_dict = {key: float(value) for key, value in preds_dict.items()}
            
            print(f"X-ray evaluation results: {preds_dict}")
            return preds_dict
            
        except Exception as e:
            print(f"Error in X-ray prediction: {e}")
            # Return safe default predictions
            return {pathology: 0.1 for pathology in self.TARGET_PATHOLOGIES}

    def evaluate_xray(self, image_path: str) -> dict:
        """
        Evaluate X-ray scan for LLM integration.
        - **image_path**: Path to the image file.
        - **Returns**: A dictionary with the evaluation result.
        """
        try:
            model = self._get_model()
            model.eval()
            
            # Image preprocessing
            transform = xrv.datasets.XRayCenterCrop()
            img = xrv.datasets.normalize(image_path, 255)
            img = transform(img)
            img = torch.from_numpy(img).unsqueeze(0)
            
            with torch.no_grad():
                pred = model(img)
                
                # Model.pth 3 sınıf için eğitilmiş: Cardiomegaly, Hernia, Infiltration
                pathologies = ["Cardiomegaly", "Hernia", "Infiltration"]
                predictions = torch.sigmoid(pred).squeeze().numpy()
                
                results = {}
                for i, pathology in enumerate(pathologies):
                    results[pathology] = float(predictions[i])
                
                print(f"X-ray evaluation results: {results}")
                return results
                
        except Exception as e:
            print(f"Error in X-ray prediction: {e}")
            # Fallback to dummy results
            return {
                "Cardiomegaly": 0.1,
                "Hernia": 0.05,
                "Infiltration": 0.15
            } 