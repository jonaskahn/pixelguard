"""
Utility functions for image processing operations.
Centralizes common image manipulation functions to follow DRY principle.
"""

import cv2
import numpy as np


def ensure_uint8(image: np.ndarray) -> np.ndarray:
    """Convert image to uint8 format for OpenCV compatibility"""
    if image.dtype == np.uint8:
        return image

    if image.dtype in [np.int16, np.int32, np.int64]:
        # For signed integer types, handle negative values
        return np.clip(image, 0, 255).astype(np.uint8)
    elif image.dtype in [np.float32, np.float64]:
        # For float types, assume 0-1 range and scale to 0-255
        return np.clip(image * 255, 0, 255).astype(np.uint8)
    else:
        # For other types, try direct conversion
        return image.astype(np.uint8)


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale, handling various input formats"""
    image = ensure_uint8(image)

    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def ensure_3channel_bgr(image: np.ndarray) -> np.ndarray:
    """Ensure image is in 3-channel BGR format for safe reshaping operations"""
    if image is None:
        raise ValueError("Image is None")

    image = ensure_uint8(image)

    if len(image.shape) == 2:
        # Grayscale image - convert to BGR
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif len(image.shape) == 3:
        if image.shape[2] == 3:
            # Already 3-channel, assume BGR
            return image
        elif image.shape[2] == 4:
            # RGBA/BGRA image - convert to BGR (drop alpha)
            return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            raise ValueError(f"Unsupported image shape: {image.shape}")
    else:
        raise ValueError(f"Unsupported image shape: {image.shape}")


def convert_color_space(pixels: np.ndarray, color_space: str) -> np.ndarray:
    """Convert pixels to specified color space"""
    pixels = ensure_uint8(pixels)

    if color_space == "LAB":
        return cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB).reshape(-1, 3)
    elif color_space == "HSV":
        return cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
    elif color_space == "RGB":
        return cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2RGB).reshape(-1, 3)
    else:
        raise ValueError(f"Unsupported color space: {color_space}")


def extract_edge_samples(
    image: np.ndarray, height: int, width: int, sample_percentage: float
) -> np.ndarray:
    """Extract pixel samples from image edges"""
    edge_sample_height = int(height * sample_percentage)
    edge_sample_width = int(width * sample_percentage)

    top_edge = image[:edge_sample_height, :].reshape(-1, 3)
    bottom_edge = image[-edge_sample_height:, :].reshape(-1, 3)
    left_edge = image[:, :edge_sample_width].reshape(-1, 3)
    right_edge = image[:, -edge_sample_width:].reshape(-1, 3)

    return np.vstack([top_edge, bottom_edge, left_edge, right_edge])


def extract_corner_samples(
    image: np.ndarray, height: int, width: int, sample_percentage: float
) -> np.ndarray:
    """Extract pixel samples from image corners"""
    corner_height = int(height * sample_percentage)
    corner_width = int(width * sample_percentage)

    top_left = image[:corner_height, :corner_width].reshape(-1, 3)
    top_right = image[:corner_height, -corner_width:].reshape(-1, 3)
    bottom_left = image[-corner_height:, :corner_width].reshape(-1, 3)
    bottom_right = image[-corner_height:, -corner_width:].reshape(-1, 3)

    return np.vstack([top_left, top_right, bottom_left, bottom_right])


def calculate_pixel_coverage(
    pixels: np.ndarray, target_color: np.ndarray, tolerance: int
) -> float:
    """Calculate percentage of pixels similar to target color"""
    similar_pixels = np.sum(np.all(np.abs(pixels - target_color) <= tolerance, axis=1))
    return similar_pixels / len(pixels)


def validate_image(image) -> bool:
    """Validate that image is suitable for processing"""
    if image is None:
        return False
    if not hasattr(image, "shape"):
        return False
    if len(image.shape) < 2:
        return False
    return True
