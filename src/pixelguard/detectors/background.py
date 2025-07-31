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

    def detect(self, image: np.ndarray, image_path: str="") -> DetectionResult:
        if not self._validate_image(image):
            return self._create_error_result(
                ValueError("Invalid image provided"), "invalid_image"
            )

        try:
            normalized_image = self._ensure_3channel_bgr(image)
            background_analysis = self._analyze_background_dominance(normalized_image)
            actual_coverage = self._calculate_total_background_coverage(
                normalized_image, background_analysis["dominant_color"]
            )

            exceeds_threshold = (
                actual_coverage > self.config.background_coverage_threshold
            )
            detected_issues = []

            if exceeds_threshold:
                detected_issues.append(
                    f"Background dominates {actual_coverage*100:.1f}% of image"
                )

            analysis_details = {
                "dominant_color": background_analysis["dominant_color"].tolist(),
                "coverage_percentage": actual_coverage,
                "detection_method": background_analysis["detection_method"],
            }

            detection_confidence = actual_coverage

            return self._create_result(exceeds_threshold, detection_confidence, analysis_details, detected_issues)

        except Exception as e:
            return self._create_error_result(e, "background_detection_error")

    def _analyze_background_dominance(self, image: np.ndarray) -> Dict[str, Any]:
        if self.config.detection_method == "edge_based":
            return self._analyze_background_from_edges(image)
        elif self.config.detection_method == "corner_based":
            return self._analyze_background_from_corners(image)
        else:
            return self._analyze_background_from_histogram(image)

    def _analyze_background_from_edges(self, image: np.ndarray) -> Dict[str, Any]:
        try:
            height, width = image.shape[:2]

            edge_pixel_samples = extract_edge_samples(
                image, height, width, self.config.edge_sample_percentage
            )
            most_common_color = self._find_dominant_color_with_kmeans(
                edge_pixel_samples, n_clusters=1
            )

            edge_coverage_percentage = calculate_pixel_coverage(
                edge_pixel_samples, most_common_color, self.config.background_color_tolerance
            )

            return {
                "dominant_color": most_common_color,
                "edge_coverage": edge_coverage_percentage,
                "detection_method": "edge_based",
                "sample_count": len(edge_pixel_samples),
            }

        except Exception as e:
            return self._create_fallback_background_result("edge_based", str(e))

    def _find_dominant_color_with_kmeans(
        self, pixels: np.ndarray, n_clusters: int=1
    ) -> np.ndarray:
        """Find dominant color using K-means clustering"""
        # Validate input data
        if len(pixels) == 0:
            return np.array([0, 0, 0], dtype=int)
        
        # Remove invalid values (NaN, inf)
        valid_mask = np.isfinite(pixels).all(axis=1)
        valid_pixels = pixels[valid_mask]
        
        if len(valid_pixels) == 0:
            return np.array([0, 0, 0], dtype=int)
        
        # Ensure we have enough samples for clustering
        if len(valid_pixels) < n_clusters:
            # Return mean color if insufficient samples
            return np.mean(valid_pixels, axis=0).astype(int)
        
        # Suppress sklearn warnings for this operation
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            try:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                kmeans.fit(valid_pixels)
                return kmeans.cluster_centers_[0].astype(int)
            except Exception:
                # Fallback to mean color if clustering fails
                return np.mean(valid_pixels, axis=0).astype(int)

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
        try:
            height, width = image.shape[:2]

            corner_pixel_samples = extract_corner_samples(
                image, height, width, self.config.corner_sample_percentage
            )
            most_common_color = self._find_dominant_color_with_kmeans(
                corner_pixel_samples, n_clusters=1
            )

            corner_coverage_percentage = calculate_pixel_coverage(
                corner_pixel_samples, most_common_color, self.config.background_color_tolerance
            )

            return {
                "dominant_color": most_common_color,
                "corner_coverage": corner_coverage_percentage,
                "detection_method": "corner_based",
                "sample_count": len(corner_pixel_samples),
            }

        except Exception as e:
            return self._create_fallback_background_result("corner_based", str(e))

    def _analyze_background_from_histogram(self, image: np.ndarray) -> Dict[str, Any]:
        try:
            normalized_image = ensure_uint8(image)

            lab_color_space_image = cv2.cvtColor(normalized_image, cv2.COLOR_BGR2LAB)

            all_pixels = normalized_image.reshape(-1, 3)
            lab_pixels = lab_color_space_image.reshape(-1, 3)

            most_frequent_color_lab, frequency_percentage = (
                self._find_dominant_color_from_histogram(lab_pixels)
            )
            most_frequent_color_bgr = self._convert_lab_to_bgr(most_frequent_color_lab)

            return {
                "dominant_color": most_frequent_color_bgr,
                "histogram_coverage": frequency_percentage,
                "detection_method": "histogram_based",
                "total_pixels": len(all_pixels),
            }

        except Exception as e:
            return self._create_fallback_background_result("histogram_based", str(e))

    def _find_dominant_color_from_histogram(
        self, lab_pixels: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        if len(lab_pixels) == 0:
            return np.array([50, 0, 0]), 0.0
        
        valid_mask = np.isfinite(lab_pixels).all(axis=1)
        valid_pixels = lab_pixels[valid_mask]
        
        if len(valid_pixels) == 0:
            return np.array([50, 0, 0]), 0.0
        
        cluster_count = min(3, len(valid_pixels))
        if cluster_count < 1:
            return np.mean(valid_pixels, axis=0), 1.0
        
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            try:
                kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
                kmeans.fit(valid_pixels)

                cluster_labels = kmeans.labels_
                unique_labels, counts = np.unique(cluster_labels, return_counts=True)

                most_frequent_cluster_index = np.argmax(counts)
                most_frequent_color_lab = kmeans.cluster_centers_[most_frequent_cluster_index]
                frequency_percentage = counts[most_frequent_cluster_index] / len(valid_pixels)

                return most_frequent_color_lab, frequency_percentage
            except Exception:
                return np.mean(valid_pixels, axis=0), 1.0

    def _convert_lab_to_bgr(self, lab_color: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(np.uint8([[lab_color]]), cv2.COLOR_LAB2BGR)[0][0]

    def _calculate_total_background_coverage(
        self, image: np.ndarray, dominant_color: np.ndarray
    ) -> float:
        normalized_image = ensure_uint8(image)

        all_pixels = normalized_image.reshape(-1, 3)
        lab_color_space_image = cv2.cvtColor(normalized_image, cv2.COLOR_BGR2LAB)

        dominant_color_uint8 = ensure_uint8(dominant_color.reshape(1, 1, 3))
        lab_dominant_color = cv2.cvtColor(
            dominant_color_uint8, cv2.COLOR_BGR2LAB
        ).reshape(3)

        lab_pixels = lab_color_space_image.reshape(-1, 3)
        color_distances = np.linalg.norm(lab_pixels - lab_dominant_color, axis=1)

        matching_pixels_count = np.sum(color_distances <= self.config.background_color_tolerance)
        return matching_pixels_count / len(all_pixels)
