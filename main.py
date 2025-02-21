from fastapi import FastAPI, UploadFile, File
import tensorflow as tf
import numpy as np
import json
from PIL import Image
import io

# Lade das Modell und die Labels
model = tf.keras.models.load_model("final_model.keras")
print("✅ Model successfully loaded!")

with open("class_labels.json", "r") as f:
    class_labels = json.load(f)
print("✅ Labels successfully loaded:", class_labels)

IMAGE_SIZE = 224
app = FastAPI()

def preprocess_image(image: Image.Image):
    image = image.resize((IMAGE_SIZE, IMAGE_SIZE))
    img_array = np.array(image) / 255.0  # Normalisierung
    img_array = np.expand_dims(img_array, axis=0)  # Batch Dimension hinzufügen
    return img_array

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read()))
    img_array = preprocess_image(image)

    predictions = model.predict(img_array)
    predicted_class = np.argmax(predictions)
    confidence = np.max(predictions)

    if 0 <= predicted_class < len(class_labels):
        return {"class": class_labels[str(predicted_class)], "confidence": float(confidence)}
    else:
        return {"error": f"Predicted class {predicted_class} is out of valid range!"}
