import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

# Load the model once (Global variable to avoid reloading it 100 times)
print("🧠 Loading AI Model (CLIP)... this might take a minute...")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def get_text_embedding(text):
    """Converts a search query (e.g., 'aggressive defense') into numbers."""
    inputs = processor(text=[text], return_tensors="pt", padding=True)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
    return text_features[0].tolist() # Convert tensor to standard list

def get_image_embedding(image_path_or_url):
    """Converts an image into numbers."""
    if isinstance(image_path_or_url, str):
        # If it's a URL or path, open it. 
        # Note: For URLs, you'd need requests.get(), but we'll assume local paths for now
        image = Image.open(image_path_or_url)
    else:
        image = image_path_or_url

    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
    return image_features[0].tolist()
