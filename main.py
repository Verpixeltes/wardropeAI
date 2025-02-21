from fastapi import FastAPI, UploadFile, File
import tensorflow as tf
import numpy as np
import json
from PIL import Image
import io

# Deaktiviere die GPU-Nutzung, falls keine GPU verfügbar ist
tf.config.set_visible_devices([], 'GPU')

# Lade das Modell und die Labels
model = tf.keras.models.load_model("final_model.keras")
print("✅ Model successfully loaded!")

with open("class_labels.json", "r") as f:
    class_labels = json.load(f)
print("✅ Labels successfully loaded:", class_labels)

IMAGE_SIZE = 224  # Bildgröße, auf die alle Bilder skaliert werden
app = FastAPI()

# TensorFlow Speicheroptimierung: Verwende nur so viel GPU-Speicher wie notwendig
physical_devices = tf.config.list_physical_devices('CPU')
if physical_devices:
    tf.config.set_logical_device_configuration(physical_devices[0], [tf.config.LogicalDeviceConfiguration(memory_limit=1024)])

# Bildvorverarbeitung
def preprocess_image(image: Image.Image):
    image = image.resize((IMAGE_SIZE, IMAGE_SIZE))
    img_array = np.array(image) / 255.0  # Normalisierung
    img_array = np.expand_dims(img_array, axis=0)  # Batch Dimension hinzufügen
    return img_array

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    # Bild aus der hochgeladenen Datei laden
    image = Image.open(io.BytesIO(await file.read()))
    
    # Bild vorverarbeiten
    img_array = preprocess_image(image)

    # Vorhersage durchführen
    predictions = model.predict(img_array)
    predicted_class = np.argmax(predictions)
    confidence = np.max(predictions)

    # Rückgabe der Vorhersage
    if 0 <= predicted_class < len(class_labels):
        return {"class": class_labels[str(predicted_class)], "confidence": float(confidence)}
    else:
        return {"error": f"Predicted class {predicted_class} is out of valid range!"}
