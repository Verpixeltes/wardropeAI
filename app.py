import tensorflow as tf
import numpy as np
import json
from fastapi import FastAPI, UploadFile, File
from PIL import Image
import io

# Modell & Labels laden
model = tf.keras.models.load_model("model.keras")
with open("class_labels.json", "r") as f:
    class_labels = json.load(f)

# Bildverarbeitung
IMAGE_SIZE = 224
app = FastAPI()

def preprocess_image(image):
    img = image.resize((IMAGE_SIZE, IMAGE_SIZE))
    img_array = np.array(img) / 255.0  # Normalisierung
    img_array = np.expand_dims(img_array, axis=0)  # Batch-Dimension hinzufügen
    return img_array

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    img_array = preprocess_image(image)

    # Vorhersage
    predictions = model.predict(img_array)
    predicted_class = np.argmax(predictions)
    confidence = np.max(predictions)

    if 0 <= predicted_class < len(class_labels):
        result = {
            "category": class_labels[str(predicted_class)],
            "confidence": f"{confidence:.2%}"
        }
    else:
        result = {"error": "Ungültige Klassenvorhersage!"}

    return result
