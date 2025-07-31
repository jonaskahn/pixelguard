import numpy as np
from sklearn.cluster import KMeans

from .base import BaseDetector
from ..core.config import UniformColorConfig
from ..utils.image_utils import convert_color_space


class UniformColorDetector(BaseDetector):

    def __init__(self, config: UniformColorConfig):
        super().__init__("uniform_color", config)
        self.config: UniformColorConfig = config

    def detect(self, image, image_path=""):
        """Detect uniform color dominance in image"""
        if not self._validate_image(image):
            return self._create_error_result(
                ValueError("Invalid image provided"), "invalid_image"
            )

        try:
            image = self._ensure_3channel_bgr(image)
            height, width = image.shape[:2]
            total_pixels = height * width

            sample_pixels = self._extract_sample_pixels(image)
            color_space_pixels = self._convert_to_color_space(sample_pixels)
            dominant_color = self._find_dominant_color_with_kmeans(color_space_pixels)

            uniform_coverage = self._calculate_uniform_coverage(
                color_space_pixels, dominant_color
            )

            is_problematic = uniform_coverage >= self.config.uniform_coverage_threshold
            confidence = uniform_coverage

            details = self._build_analysis_details(
                uniform_coverage, dominant_color, len(sample_pixels), total_pixels
            )

            issues = []
            if is_problematic:
                issues.append(
                    f"Image is {uniform_coverage:.1%} uniform color "
                    f"(threshold: {self.config.uniform_coverage_threshold:.1%})"
                )

            return self._create_result(is_problematic, confidence, details, issues)

        except Exception as e:
            return self._create_error_result(e, "uniform_color_detection_error")

    def _extract_sample_pixels(self, image: np.ndarray) -> np.ndarray:
        """Extract pixel samples from image, optionally ignoring edges"""
        height, width = image.shape[:2]

        if self.config.ignore_edges:
            margin_height = int(height * self.config.edge_ignore_percentage)
            margin_width = int(width * self.config.edge_ignore_percentage)
            cropped = image[margin_height:-margin_height, margin_width:-margin_width]
            pixels = cropped.reshape(-1, 3)
        else:
            pixels = image.reshape(-1, 3)

        return self._sample_pixels_if_needed(pixels)

    def _sample_pixels_if_needed(self, pixels: np.ndarray) -> np.ndarray:
        """Sample pixels if total count exceeds sample size limit"""
        if len(pixels) > self.config.sample_size:
            indices = np.random.choice(
                len(pixels), self.config.sample_size, replace=False
            )
            return pixels[indices]
        return pixels

    def _convert_to_color_space(self, pixels: np.ndarray) -> np.ndarray:
        """Convert pixels to specified color space for analysis"""
        return convert_color_space(pixels, self.config.color_space)

    def _find_dominant_color_with_kmeans(
        self, color_space_pixels: np.ndarray
    ) -> np.ndarray:
        """Find dominant color using K-means clustering"""
        kmeans = KMeans(n_clusters=1, random_state=42, n_init=10)
        kmeans.fit(color_space_pixels)
        return kmeans.cluster_centers_[0]

    def _calculate_uniform_coverage(
        self, color_space_pixels: np.ndarray, dominant_color: np.ndarray
    ) -> float:
        """Calculate percentage of pixels similar to dominant color"""
        color_delta = self.config.color_delta_threshold
        similar_pixels = np.sum(
            np.all(np.abs(color_space_pixels - dominant_color) <= color_delta, axis=1)
        )
        return similar_pixels / len(color_space_pixels)

    def _build_analysis_details(
        self,
        uniform_coverage: float,
        dominant_color: np.ndarray,
        sample_size: int,
        total_pixels: int,
    ) -> dict:
        """Build detailed analysis results dictionary"""
        return {
            "uniform_coverage": uniform_coverage,
            "dominant_color": dominant_color.tolist(),
            "color_space": self.config.color_space,
            "sample_size": sample_size,
            "total_pixels": total_pixels,
            "color_delta_threshold": self.config.color_delta_threshold,
            "uniform_coverage_threshold": self.config.uniform_coverage_threshold,
        }
