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
        if not self._validate_image(image):
            return self._create_error_result(
                ValueError("Invalid image provided"), "invalid_image"
            )

        try:
            normalized_image = self._ensure_3channel_bgr(image)
            height, width = normalized_image.shape[:2]
            total_pixel_count = height * width

            sampled_pixels = self._extract_representative_pixels(normalized_image)
            color_space_pixels = self._convert_to_target_color_space(sampled_pixels)
            most_common_color = self._find_dominant_color_with_kmeans(
                color_space_pixels
            )

            uniformity_percentage = self._calculate_color_uniformity_coverage(
                color_space_pixels, most_common_color
            )

            exceeds_threshold = (
                uniformity_percentage >= self.config.uniform_coverage_threshold
            )
            detection_confidence = uniformity_percentage

            analysis_details = self._build_uniformity_analysis_details(
                uniformity_percentage,
                most_common_color,
                len(sampled_pixels),
                total_pixel_count,
            )

            detected_issues = []
            if exceeds_threshold:
                detected_issues.append(
                    f"Image is {uniformity_percentage:.1%} uniform color "
                    f"(threshold: {self.config.uniform_coverage_threshold:.1%})"
                )

            return self._create_result(
                exceeds_threshold,
                detection_confidence,
                analysis_details,
                detected_issues,
            )

        except Exception as e:
            return self._create_error_result(e, "uniform_color_detection_error")

    def _extract_representative_pixels(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]

        if self.config.ignore_edges:
            vertical_margin = int(height * self.config.edge_ignore_percentage)
            horizontal_margin = int(width * self.config.edge_ignore_percentage)
            interior_region = image[
                vertical_margin:-vertical_margin, horizontal_margin:-horizontal_margin
            ]
            all_pixels = interior_region.reshape(-1, 3)
        else:
            all_pixels = image.reshape(-1, 3)

        return self._limit_sample_size_if_needed(all_pixels)

    def _limit_sample_size_if_needed(self, pixels: np.ndarray) -> np.ndarray:
        if len(pixels) > self.config.sample_size:
            random_indices = np.random.choice(
                len(pixels), self.config.sample_size, replace=False
            )
            return pixels[random_indices]
        return pixels

    def _convert_to_target_color_space(self, pixels: np.ndarray) -> np.ndarray:
        return convert_color_space(pixels, self.config.color_space)

    def _find_dominant_color_with_kmeans(
        self, color_space_pixels: np.ndarray
    ) -> np.ndarray:
        if len(color_space_pixels) == 0:
            return np.array([0, 0, 0])

        valid_mask = np.isfinite(color_space_pixels).all(axis=1)
        valid_pixels = color_space_pixels[valid_mask]

        if len(valid_pixels) == 0:
            return np.array([0, 0, 0])

        if len(valid_pixels) < 2:
            return np.mean(valid_pixels, axis=0)

        import warnings

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            try:
                kmeans = KMeans(n_clusters=1, random_state=42, n_init=10)
                kmeans.fit(valid_pixels)
                return kmeans.cluster_centers_[0]
            except Exception:
                return np.mean(valid_pixels, axis=0)

    def _calculate_color_uniformity_coverage(
        self, color_space_pixels: np.ndarray, most_common_color: np.ndarray
    ) -> float:
        if len(color_space_pixels) == 0:
            return 0.0

        valid_pixel_mask = (
            np.isfinite(color_space_pixels).all(axis=1)
            & np.isfinite(most_common_color).all()
        )
        if not valid_pixel_mask.any():
            return 0.0

        valid_pixels = color_space_pixels[valid_pixel_mask]
        if len(valid_pixels) == 0:
            return 0.0

        color_tolerance = self.config.color_delta_threshold
        matching_pixels_count = np.sum(
            np.all(np.abs(valid_pixels - most_common_color) <= color_tolerance, axis=1)
        )
        return matching_pixels_count / len(valid_pixels)

    def _build_uniformity_analysis_details(
        self,
        uniformity_percentage: float,
        most_common_color: np.ndarray,
        sample_count: int,
        total_pixel_count: int,
    ) -> dict:
        return {
            "uniformity_percentage": uniformity_percentage,
            "most_common_color": most_common_color.tolist(),
            "color_space": self.config.color_space,
            "sample_count": sample_count,
            "total_pixel_count": total_pixel_count,
            "color_tolerance": self.config.color_delta_threshold,
            "threshold": self.config.uniform_coverage_threshold,
        }
