from pathlib import Path

import cv2
import numpy as np

from .image_utils import ensure_uint8


class ImageLoader:
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    last_loaded_path = None

    def load(self, image_path) -> np.ndarray:
        self.last_loaded_path = image_path
        image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Ensure image is in uint8 format for compatibility with OpenCV operations
        return ensure_uint8(image)

    def is_supported_format(self, path) -> bool:
        return Path(path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def get_image_information(self, path):
        image = self.load(path)
        return {"shape": image.shape, "dtype": image.dtype}
