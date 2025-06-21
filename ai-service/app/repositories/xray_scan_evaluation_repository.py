import numpy as np
import torch
import torchxrayvision as xrv
import torchvision
import os


class XRayScanEvaluationRepository:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(XRayScanEvaluationRepository, cls).__new__(cls)
        return cls._instance

    def _get_model(self):
        if self._model is None:
            # 1. Get the base model architecture
            model = xrv.models.get_model("densenet121-res224-all")

            # 2. Define the path to the fine-tuned model inside the container
            model_path = "/app/models/model.pth" 

            # 3. Load the fine-tuned weights if the model file exists
            if os.path.exists(model_path):
                try:
                    # Load weights onto the CPU
                    state_dict = torch.load(model_path, map_location=torch.device('cpu'))
                    model.load_state_dict(state_dict)
                    print("Successfully loaded fine-tuned model from model.pth")
                except Exception as e:
                    print(f"Error loading fine-tuned model: {e}. Falling back to pretrained model.")
            else:
                print(f"Fine-tuned model not found at {model_path}. Using pretrained torchxrayvision model.")
            
            self._model = model
        return self._model

    # Prediction function for X-ray classification
    def __get_xray_prediction(self, image: np.array, cuda: bool = False):
        # Load the X-ray model (either fine-tuned or pretrained)
        xray_model = self._get_model()
        
        # Move model to appropriate device
        device = torch.device("cuda" if cuda and torch.cuda.is_available() else "cpu")
        xray_model.to(device)
        xray_model.eval()

        image = xrv.datasets.normalize(image, 255)

        if len(image.shape) > 2:
            image = image[:, :, 0]  # Use the first channel if RGB
        if len(image.shape) < 2:
            raise ValueError("Error: Image is not valid.")

        image = image[None, :, :]  # Add batch dimension
        transform = torchvision.transforms.Compose(
            [xrv.datasets.XRayCenterCrop(), xrv.datasets.XRayResizer(224)],
            )
        image = transform(image)
        
        image = torch.from_numpy(image).unsqueeze(0).to(device)

        with torch.no_grad():
            preds = xray_model(image).cpu()

        preds_dict = dict(zip(
            xray_model.pathologies, 
            preds[0].detach().numpy(),
        ))
        
        # Convert NumPy objects to native Python types for serialization
        preds_dict = {key: float(value) if isinstance(value, np.float32) else value for key, value in preds_dict.items()}
        
        return preds_dict


    def evaluate_xray_scan(
            self, 
            xray_scan: np.array,
        ) -> dict:
        """
        Evaluate X-ray scan and provide diagnosis.
        - **xray_scan**: The X-ray scan file to be evaluated.
        - **Returns**: A JSON response with the evaluation result.
        - **Raises**: 400 if the input is invalid, 500 for internal server errors.
        """
        result = self.__get_xray_prediction(xray_scan, cuda=torch.cuda.is_available())
        if result is None:
            raise ValueError("Error: Image is not valid.")
        return result 