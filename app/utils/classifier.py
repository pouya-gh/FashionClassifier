import torch
from torchvision import models, transforms

from PIL import Image

from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent / "data" / "mobilenet.pth"

classifier_model = models.mobilenet_v2().to("cpu")
classifier_model.classifier[1] = torch.nn.Linear(1280, 10).to("cpu")
classifier_model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))


FAHION_MNIST_CLASS_NAMES = [
    "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
    "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"
]


def classify_image(image_path: str) -> int:
    img = Image.open(image_path).convert("RGB")

    transform = transforms.Compose([
            transforms.Grayscale(3),
            transforms.Resize((28, 28)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ])
    
    pred_index = -1
    classifier_model.eval()
    with torch.inference_mode():
        pred = classifier_model(transform(img).unsqueeze(0))
        pred_index = torch.softmax(pred, 1).argmax()

    return pred_index