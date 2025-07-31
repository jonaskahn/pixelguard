from typing import Any, Dict, Tuple

import cv2
import numpy as np
from sklearn.cluster import KMeans

from .base import BaseDetector
from ..core.config import BackgroundDetectionConfig
from ..core.models import DetectionResult
from ..utils.image_utils import (
    ensure_uint8,
    extract_edge_samples,
    extract_corner_samples,
    calculate_pixel_coverage,
)


class BackgroundDetector(BaseDetector):

    def __init__(self, config: BackgroundDetectionConfig):
        super().__init__("background", config)
        self.config: BackgroundDetectionConfig = config

    def detect(self, image: np.ndarray, image_path: str = "") -> DetectionResult:
        if not self._validate_image(image):
            return self._create_error_result(
                ValueError("Invalid image provided"), "invalid_image"
            )

        try:
            image = self._ensure_3channel_bgr(image)
            background_analysis = self._analyze_background(image)
            background_coverage = self._calculate_background_coverage(
                image, background_analysis["background_color"]
            )

            is_problematic = (
                background_coverage > self.config.background_coverage_threshold
            )
            issues = []

            if is_problematic:
                issues.append(
                    f"Background dominates {background_coverage*100:.1f}% of image"
                )

            details = {
                "background_color": background_analysis["background_color"].tolist(),
                "background_coverage": background_coverage,
                "detection_method": background_analysis["detection_method"],
            }

            confidence = background_coverage

            return self._create_result(is_problematic, confidence, details, issues)

        except Exception as e:
            return self._create_error_result(e, "background_detection_error")

    def _analyze_background(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze background using the configured detection method"""
        if self.config.detection_method == "edge_based":
            return self._analyze_background_from_edges(image)
        elif self.config.detection_method == "corner_based":
            return self._analyze_background_from_corners(image)
        else:
            return self._analyze_background_from_histogram(image)

    def _analyze_background_from_edges(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze background dominance using edge sampling"""
        try:
            height, width = image.shape[:2]

            edge_samples = extract_edge_samples(
                image, height, width, self.config.edge_sample_percentage
            )
            dominant_color = self._find_dominant_color_with_kmeans(
                edge_samples, n_clusters=1
            )

            background_coverage = calculate_pixel_coverage(
                edge_samples, dominant_color, self.config.background_color_tolerance
            )

            return {
                "background_color": dominant_color,
                "background_coverage": background_coverage,
                "detection_method": "edge_based",
                "edge_sample_count": len(edge_samples),
            }

        except Exception as e:
            return self._create_fallback_background_result("edge_based", str(e))

    def _find_dominant_color_with_kmeans(
        self, pixels: np.ndarray, n_clusters: int = 1
    ) -> np.ndarray:
        """Find dominant color using K-means clustering"""
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(pixels)
        return kmeans.cluster_centers_[0].astype(int)

    def _create_fallback_background_result(
        self, method: str, error: str
    ) -> Dict[str, Any]:
        """Create fallback result when background analysis fails"""
        return {
            "background_color": np.array([0, 0, 0]),
            "background_coverage": 0.0,
            "detection_method": method,
            "error": error,
        }

    def _analyze_background_from_corners(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze background dominance using corner sampling"""
        try:
            height, width = image.shape[:2]

            corner_samples = extract_corner_samples(
                image, height, width, self.config.corner_sample_percentage
            )
            dominant_color = self._find_dominant_color_with_kmeans(
                corner_samples, n_clusters=1
            )

            background_coverage = calculate_pixel_coverage(
                corner_samples, dominant_color, self.config.background_color_tolerance
            )

            return {
                "background_color": dominant_color,
                "background_coverage": background_coverage,
                "detection_method": "corner_based",
                "corner_sample_count": len(corner_samples),
            }

        except Exception as e:
            return self._create_fallback_background_result("corner_based", str(e))

    def _analyze_background_from_histogram(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze background dominance using histogram analysis"""
        try:
            image = ensure_uint8(image)

            lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

            pixels = image.reshape(-1, 3)
            lab_pixels = lab_image.reshape(-1, 3)

            dominant_color_lab, dominant_coverage = (
                self._find_dominant_color_from_histogram(lab_pixels)
            )
            dominant_color_bgr = self._convert_lab_to_bgr(dominant_color_lab)

            return {
                "background_color": dominant_color_bgr,
                "background_coverage": dominant_coverage,
                "detection_method": "histogram_based",
                "total_pixels": len(pixels),
            }

        except Exception as e:
            return self._create_fallback_background_result("histogram_based", str(e))

    def _find_dominant_color_from_histogram(
        self, lab_pixels: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        """Find dominant color and coverage from histogram analysis"""
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(lab_pixels)

        cluster_labels = kmeans.labels_
        unique_labels, counts = np.unique(cluster_labels, return_counts=True)

        dominant_cluster_idx = np.argmax(counts)
        dominant_color_lab = kmeans.cluster_centers_[dominant_cluster_idx]
        dominant_coverage = counts[dominant_cluster_idx] / len(lab_pixels)

        return dominant_color_lab, dominant_coverage

    def _convert_lab_to_bgr(self, lab_color: np.ndarray) -> np.ndarray:
        """Convert LAB color to BGR format"""
        return cv2.cvtColor(np.uint8([[lab_color]]), cv2.COLOR_LAB2BGR)[0][0]

    def _calculate_background_coverage(
        self, image: np.ndarray, background_color: np.ndarray
    ) -> float:
        """Calculate background coverage across entire image"""
        image = ensure_uint8(image)

        pixels = image.reshape(-1, 3)
        lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        background_color_uint8 = ensure_uint8(background_color.reshape(1, 1, 3))
        lab_background = cv2.cvtColor(
            background_color_uint8, cv2.COLOR_BGR2LAB
        ).reshape(3)

        lab_pixels = lab_image.reshape(-1, 3)
        distances = np.linalg.norm(lab_pixels - lab_background, axis=1)

        background_pixels = np.sum(distances <= self.config.background_color_tolerance)
        return background_pixels / len(pixels)
