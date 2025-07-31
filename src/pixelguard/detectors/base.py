from abc import ABC, abstractmethod
from typing import Any, Optional

import numpy as np

from ..utils.image_utils import ensure_3channel_bgr, validate_image


class BaseDetector(ABC):

    def __init__(self, name: str, config: Any = None):
        self.name = name
        self.config = config

    @abstractmethod
    def detect(self, image, image_path=""):
        pass

    def _ensure_3channel_bgr(self, image: np.ndarray) -> np.ndarray:
        """Ensure image is in 3-channel BGR format for safe reshaping operations"""
        return ensure_3channel_bgr(image)

    def _create_result(
        self,
        is_problematic: bool,
        confidence: float,
        details: Optional[dict] = None,
        issues: Optional[list] = None,
    ):
        from src.pixelguard.core.models import DetectionResult

        return DetectionResult(
            detector_name=self.name,
            is_problematic=is_problematic,
            confidence=max(0.0, min(1.0, confidence)),
            details=details or {},
            issues=issues or [],
        )

    def _create_error_result(
        self, error: Exception, error_type: str = "detection_error"
    ):
        return self._create_result(
            is_problematic=True,
            confidence=1.0,
            details={"error_type": error_type, "error_message": str(error)},
            issues=[f"{self.name} detection failed: {str(error)}"],
        )

    def _validate_image(self, image) -> bool:
        return validate_image(image)
