import cv2
import numpy as np


def ensure_uint8(image: np.ndarray) -> np.ndarray:
    if image.dtype == np.uint8:
        return image

    if np.any(~np.isfinite(image)):
        image = np.where(np.isfinite(image), image, 0)

    if image.dtype in [np.int16, np.int32, np.int64]:
        return np.clip(image, 0, 255).astype(np.uint8)
    elif image.dtype in [np.float32, np.float64]:
        return np.clip(image * 255, 0, 255).astype(np.uint8)
    else:
        return np.clip(image, 0, 255).astype(np.uint8)


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    normalized_image = ensure_uint8(image)

    if len(normalized_image.shape) == 3:
        return cv2.cvtColor(normalized_image, cv2.COLOR_BGR2GRAY)
    return normalized_image


def ensure_3channel_bgr(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("Image is None")

    normalized_image = ensure_uint8(image)

    if len(normalized_image.shape) == 2:
        return cv2.cvtColor(normalized_image, cv2.COLOR_GRAY2BGR)
    elif len(normalized_image.shape) == 3:
        if normalized_image.shape[2] == 3:
            return normalized_image
        elif normalized_image.shape[2] == 4:
            return cv2.cvtColor(normalized_image, cv2.COLOR_BGRA2BGR)
        else:
            raise ValueError(f"Unsupported image shape: {normalized_image.shape}")
    else:
        raise ValueError(f"Unsupported image shape: {normalized_image.shape}")


def convert_color_space(pixels: np.ndarray, target_color_space: str) -> np.ndarray:
    if len(pixels) == 0:
        return pixels
    
    normalized_pixels = ensure_uint8(pixels)
    
    if normalized_pixels.shape[-1] != 3:
        raise ValueError(f"Expected 3-channel pixels, got shape: {normalized_pixels.shape}")

    try:
        if target_color_space == "LAB":
            return cv2.cvtColor(normalized_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB).reshape(-1, 3)
        elif target_color_space == "HSV":
            return cv2.cvtColor(normalized_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
        elif target_color_space == "RGB":
            return cv2.cvtColor(normalized_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2RGB).reshape(-1, 3)
        else:
            raise ValueError(f"Unsupported color space: {target_color_space}")
    except cv2.error:
        return normalized_pixels.astype(np.float64)


def extract_edge_samples(
    image: np.ndarray, height: int, width: int, sample_percentage: float
) -> np.ndarray:
    edge_sample_height = int(height * sample_percentage)
    edge_sample_width = int(width * sample_percentage)

    top_edge_pixels = image[:edge_sample_height,:].reshape(-1, 3)
    bottom_edge_pixels = image[-edge_sample_height:,:].reshape(-1, 3)
    left_edge_pixels = image[:,:edge_sample_width].reshape(-1, 3)
    right_edge_pixels = image[:, -edge_sample_width:].reshape(-1, 3)

    return np.vstack([top_edge_pixels, bottom_edge_pixels, left_edge_pixels, right_edge_pixels])


def extract_corner_samples(
    image: np.ndarray, height: int, width: int, sample_percentage: float
) -> np.ndarray:
    corner_region_height = int(height * sample_percentage)
    corner_region_width = int(width * sample_percentage)

    top_left_pixels = image[:corner_region_height,:corner_region_width].reshape(-1, 3)
    top_right_pixels = image[:corner_region_height, -corner_region_width:].reshape(-1, 3)
    bottom_left_pixels = image[-corner_region_height:,:corner_region_width].reshape(-1, 3)
    bottom_right_pixels = image[-corner_region_height:, -corner_region_width:].reshape(-1, 3)

    return np.vstack([top_left_pixels, top_right_pixels, bottom_left_pixels, bottom_right_pixels])


def calculate_pixel_coverage(
    pixels: np.ndarray, target_color: np.ndarray, color_tolerance: int
) -> float:
    matching_pixel_count = np.sum(np.all(np.abs(pixels - target_color) <= color_tolerance, axis=1))
    return matching_pixel_count / len(pixels)


def validate_image(image) -> bool:
    if image is None:
        return False
    if not hasattr(image, "shape"):
        return False
    if len(image.shape) < 2:
        return False
    return True
