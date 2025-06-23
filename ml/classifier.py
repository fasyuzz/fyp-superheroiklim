import os
import numpy as np
import tensorflow as tf
from PIL import Image

# Load model once (adjust path if needed)


MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model_final.h5')

print("Looking for model at:", os.path.abspath(MODEL_PATH))
print("Exists?", os.path.exists(MODEL_PATH))

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

model = tf.keras.models.load_model(MODEL_PATH)

# Match your training class names
class_labels = ['commute', 'energy', 'plants', 'recycle', 'water']  

def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224))  # Resize to match model input size
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def classify_image(image_path, theme=None):
    processed = preprocess_image(image_path)
    predictions = model.predict(processed)[0]
    confidence_scores = {
        label: float(score)
        for label, score in zip(class_labels, predictions)
    }
    predicted_index = np.argmax(predictions)
    predicted_label = class_labels[predicted_index]
    confidence = float(predictions[predicted_index])
    theme_confidence = None
    if theme and theme in confidence_scores:
        theme_confidence = confidence_scores[theme]
    return predicted_label, confidence, theme_confidence
