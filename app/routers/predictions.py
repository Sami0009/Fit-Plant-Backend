from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import logging
from PIL import Image
import numpy as np
import cv2

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

model = None

def get_model():
    global model
    if model is None:
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import BatchNormalization, Dense, Dropout
            from tensorflow.keras import regularizers
            # Load your trained model
            img_shape = (224, 224, 3)
            class_count = 38

            base_model = tf.keras.applications.EfficientNetB3(
                include_top=False,
                weights="imagenet",
                input_shape=img_shape,
                pooling='max'
            )

            model = Sequential([
                base_model,
                BatchNormalization(axis=-1, momentum=0.99, epsilon=0.001),
                Dense(256,
                      kernel_regularizer=regularizers.l2(0.016),
                      activity_regularizer=regularizers.l1(0.006),
                      bias_regularizer=regularizers.l1(0.006),
                      activation='relu'),
                Dropout(rate=0.45, seed=123),
                Dense(class_count, activation='softmax')
            ])

            model_path = "models/efficientnetb3-PlantVillageDisease-weights.h5"
            if os.path.exists(model_path):
                model.load_weights(model_path)
                logger.info("Model loaded successfully.")
            else:
                logger.error(f"Model file not found: {model_path}")
                model = None  # Set to None to indicate failure
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            model = None
    return model

# Define class names with user-friendly mapping
class_names = [
    'Apple___Apple_scab',
    'Apple___Black_rot',
    'Apple___Cedar_apple_rust',
    'Apple___healthy',
    'Blueberry___healthy',
    'Cherry_(including_sour)___Powdery_mildew',
    'Cherry_(including_sour)___healthy',
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
    'Corn_(maize)___Common_rust_',
    'Corn_(maize)___Northern_Leaf_Blight',
    'Corn_(maize)___healthy',
    'Grape___Black_rot',
    'Grape___Esca_(Black_Measles)',
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
    'Grape___healthy',
    'Orange___Haunglongbing_(Citrus_greening)',
    'Peach___Bacterial_spot',
    'Peach___healthy',
    'Pepper,_bell___Bacterial_spot',
    'Pepper,_bell___healthy',
    'Potato___Early_blight',
    'Potato___Late_blight',
    'Potato___healthy',
    'Raspberry___healthy',
    'Soybean___healthy',
    'Squash___Powdery_mildew',
    'Strawberry___Leaf_scorch',
    'Strawberry___healthy',
    'Tomato___Bacterial_spot',
    'Tomato___Early_blight',
    'Tomato___Late_blight',
    'Tomato___Leaf_Mold',
    'Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites Two-spotted_spider_mite',
    'Tomato___Target_Spot',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato___Tomato_mosaic_virus',
    'Tomato___healthy'
]

friendly_names = {cls: cls.replace('___', ' ').replace('_', ' ').replace('(including sour)', '').replace(', bell', '').strip().title() for cls in class_names}

# Processed images folder
PROCESSED_DIR = "processed_images"
os.makedirs(PROCESSED_DIR, exist_ok=True)

def is_leaf_image(save_path):
    """
    Detect if the image contains a leaf using OpenCV.
    Returns True if leaf detected, False otherwise.
    """
    # Load image with OpenCV
    img = cv2.imread(save_path)
    if img is None:
        logger.error("Failed to load image for leaf detection")
        return False

    # Resize for faster processing
    height, width = img.shape[:2]
    if max(height, width) > 500:
        scale = 500 / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height))

    # Convert to HSV for color segmentation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Wider HSV range for green/yellow/brown leaves
    lower_green = np.array([10, 30, 30])  # Include yellow/brown hues
    upper_green = np.array([100, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Morphological operations to reduce noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Calculate mask coverage (fraction of leaf-like pixels)
    mask_coverage = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])
    logger.info(f"Mask coverage: {mask_coverage:.3f}")

    # Edge detection on the mask
    edges = cv2.Canny(mask, 50, 150)
    edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
    logger.info(f"Edge density: {edge_density:.3f}")

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    logger.info(f"Found {len(contours)} contours")

    # Relaxed check: Pass if either edge density or contour features suggest a leaf
    if edge_density >= 0.02 or mask_coverage >= 0.1:  # Lowered edge density threshold
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 500:  # Reduced min area for smaller leaves
                continue

            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter ** 2)
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h

            # Log contour details
            logger.info(f"Contour: Area={area:.0f}, Circularity={circularity:.3f}, Aspect={aspect_ratio:.3f}")

            # Relaxed shape checks
            if (0.2 <= circularity <= 1.0) and (0.1 <= aspect_ratio <= 5.0):
                logger.info(f"Leaf detected: Area={area:.0f}, Circularity={circularity:.3f}, Aspect={aspect_ratio:.3f}, Edges={edge_density:.3f}")
                return True

    logger.warning("Rejected: No leaf-like features (low edge density or no valid contours)")
    return False

@router.post("/predict/")
async def predict(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file: {file.filename}")
        contents = await file.read()

        # Save uploaded image
        filename = f"{uuid.uuid4()}.jpg"
        save_path = os.path.join(PROCESSED_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(contents)

        # Check if it's a leaf
        if not is_leaf_image(save_path):
            logger.warning("Image rejected: Not a plant leaf")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Image does not appear to be a plant leaf. Please upload a clear plant leaf image."
                }
            )

        # Proceed with preprocessing and prediction
        from tensorflow.keras.preprocessing import image
        img = image.load_img(save_path, target_size=(224, 224), color_mode="rgb")
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)

        # Predict
        model_instance = get_model()
        if model_instance is None:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Model not available. Please check server configuration."
                }
            )
        predictions = model_instance.predict(img_array)
        predicted_index = np.argmax(predictions, axis=1)[0]
        predicted_class = class_names[predicted_index]
        confidence = float(np.max(predictions))
        friendly_prediction = friendly_names.get(predicted_class, predicted_class)

        logger.info(f"Predictions array: {predictions}")
        logger.info(f"Predicted index: {predicted_index}, Class: {predicted_class}")
        logger.info(f"Prediction: {friendly_prediction}, Confidence: {confidence:.3f}")

        # Top 3 predictions
        top_indices = np.argsort(predictions[0])[::-1][:3]
        logger.info("Top 3 predictions:")
        top_predictions = []
        for i, idx in enumerate(top_indices):
            pred_name = friendly_names.get(class_names[idx], class_names[idx])
            pred_conf = float(predictions[0][idx])
            top_predictions.append({"name": pred_name, "confidence": round(pred_conf * 100, 2)})
            logger.info(f"{i+1}. {pred_name}: {pred_conf:.3f}")

        return {
            "prediction": friendly_prediction,
            "confidence": round(confidence * 100, 2),
            "cropped_image_url": f"/processed_images/{filename}",
            "raw_prediction": predicted_class,
            "top_predictions": top_predictions,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Prediction failed: {str(e)}"
            }
        )
