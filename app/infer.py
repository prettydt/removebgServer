"""ONNX model loading, preprocessing, inference, and postprocessing."""
import os
import logging
from typing import Tuple
import numpy as np
import cv2
import onnxruntime as ort

logger = logging.getLogger(__name__)

# Global model session
_session = None
_model_input_name = None
_model_output_name = None


def load_model(model_path: str = "models/u2netp.onnx") -> None:
    """
    Load ONNX model with GPU support.
    
    Args:
        model_path: Path to ONNX model file
        
    Raises:
        FileNotFoundError: If model file doesn't exist
        RuntimeError: If model fails to load
    """
    global _session, _model_input_name, _model_output_name
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found: {model_path}. "
            "Please download the model and place it in the models/ directory. "
            "See README.md for instructions."
        )
    
    logger.info(f"Loading ONNX model from {model_path}")
    
    # Configure ONNX Runtime with GPU support
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    
    try:
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        _session = ort.InferenceSession(
            model_path,
            sess_options=sess_options,
            providers=providers
        )
        
        # Get input/output names
        _model_input_name = _session.get_inputs()[0].name
        _model_output_name = _session.get_outputs()[0].name
        
        # Log the provider being used
        provider = _session.get_providers()[0]
        logger.info(f"Model loaded successfully using {provider}")
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Failed to load ONNX model: {e}")


def preprocess_image(image_bytes: bytes, target_size: int = 512) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Preprocess image for model inference.
    
    Args:
        image_bytes: Raw image bytes
        target_size: Target size for longest edge
        
    Returns:
        Tuple of (preprocessed image array, original size)
        
    Raises:
        ValueError: If image cannot be decoded
    """
    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Failed to decode image. Please provide a valid image file.")
    
    original_size = img.shape[:2]  # (height, width)
    
    # Resize image while maintaining aspect ratio
    h, w = img.shape[:2]
    if max(h, w) > target_size:
        if h > w:
            new_h = target_size
            new_w = int(w * target_size / h)
        else:
            new_w = target_size
            new_h = int(h * target_size / w)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Normalize to [0, 1]
    img = img.astype(np.float32) / 255.0
    
    # Standardize (ImageNet mean and std)
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    
    # Transpose to CHW format and add batch dimension
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    
    return img, original_size


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Apply sigmoid activation function."""
    return 1 / (1 + np.exp(-x))


def postprocess_mask(mask: np.ndarray, original_size: Tuple[int, int]) -> np.ndarray:
    """
    Postprocess model output mask.
    
    Args:
        mask: Model output mask
        original_size: Original image size (height, width)
        
    Returns:
        Processed mask resized to original size
    """
    # Remove batch dimension and channel dimension
    mask = mask.squeeze()
    
    # Apply sigmoid if values are not in [0, 1] range
    if mask.min() < 0 or mask.max() > 1:
        mask = sigmoid(mask)
    
    # Resize to original size
    h, w = original_size
    mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
    
    # Ensure values are in [0, 255] range
    mask = (mask * 255).astype(np.uint8)
    
    return mask


def remove_background(image_bytes: bytes) -> bytes:
    """
    Remove background from image.
    
    Args:
        image_bytes: Input image bytes
        
    Returns:
        PNG image bytes with transparent background
        
    Raises:
        RuntimeError: If model is not loaded
        ValueError: If image processing fails
    """
    global _session, _model_input_name, _model_output_name
    
    if _session is None:
        raise RuntimeError("Model not loaded. Please ensure model is loaded at startup.")
    
    # Decode original image for final composition
    nparr = np.frombuffer(image_bytes, np.uint8)
    original_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if original_img is None:
        raise ValueError("Failed to decode image")
    
    # Preprocess image
    preprocessed, original_size = preprocess_image(image_bytes)
    
    # Run inference
    outputs = _session.run(
        [_model_output_name],
        {_model_input_name: preprocessed}
    )
    mask = outputs[0]
    
    # Postprocess mask
    mask = postprocess_mask(mask, original_size)
    
    # Convert original image from BGR to RGB
    original_img_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
    
    # Create RGBA image
    rgba = np.zeros((original_size[0], original_size[1], 4), dtype=np.uint8)
    rgba[:, :, :3] = original_img_rgb
    rgba[:, :, 3] = mask
    
    # Optional: Simple edge refinement to reduce color spill
    # Slightly erode the mask at the edges
    kernel = np.ones((3, 3), np.uint8)
    mask_refined = cv2.erode(mask, kernel, iterations=1)
    
    # Blend between original and refined mask based on confidence
    alpha_blend = mask.astype(np.float32) / 255.0
    mask_refined_float = mask_refined.astype(np.float32) / 255.0
    
    # Use refined mask for semi-transparent areas
    final_alpha = np.where(alpha_blend > 0.9, mask, mask_refined)
    rgba[:, :, 3] = final_alpha
    
    # Encode to PNG
    success, encoded = cv2.imencode('.png', cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    
    if not success:
        raise ValueError("Failed to encode image to PNG")
    
    return encoded.tobytes()


def check_model_loaded() -> bool:
    """Check if model is loaded."""
    return _session is not None
