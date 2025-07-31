from typing import Dict

import numpy as np

from .base import BaseDetector
from ..core.config import BorderFillConfig
from ..core.models import DetectionResult
from ..utils.image_utils import convert_to_grayscale


class BorderFillDetector(BaseDetector):

    def __init__(self, config: BorderFillConfig):
        super().__init__("border_fill", config)
        self.config: BorderFillConfig = config

    def detect(self, image: np.ndarray, image_path: str = "") -> DetectionResult:
        if not self._validate_image(image):
            return self._create_error_result(
                ValueError("Invalid image provided"), "invalid_image"
            )

        try:
            grayscale_image = self._convert_to_grayscale(image)
            height, width = grayscale_image.shape

            detected_issues = []
            analysis_details = {}
            problematic_region_count = 0

            if self.config.check_top:
                top_border_analysis = self._analyze_border_region(
                    grayscale_image, "top", height, width
                )
                analysis_details["top_border"] = top_border_analysis
                if top_border_analysis["is_problematic"]:
                    detected_issues.extend(top_border_analysis["issues"])
                    problematic_region_count += 1

            if self.config.check_bottom:
                bottom_border_analysis = self._analyze_border_region(
                    grayscale_image, "bottom", height, width
                )
                analysis_details["bottom_border"] = bottom_border_analysis
                if bottom_border_analysis["is_problematic"]:
                    detected_issues.extend(bottom_border_analysis["issues"])
                    problematic_region_count += 1

            has_border_issues = len(detected_issues) > 0
            detection_confidence = self._calculate_confidence_score(
                problematic_region_count
            )

            return self._create_result(
                has_border_issues,
                detection_confidence,
                analysis_details,
                detected_issues,
            )

        except Exception as e:
            return self._create_error_result(e, "border_fill_error")

    def _convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        return convert_to_grayscale(image)

    def _analyze_border_region(
        self, grayscale_image: np.ndarray, region_name: str, height: int, width: int
    ) -> Dict:
        region_pixels = self._extract_region_pixels(
            grayscale_image, region_name, height, width
        )
        total_pixel_count = region_pixels.size

        black_fill_percentage = self._calculate_black_pixel_percentage(
            region_pixels, total_pixel_count
        )

        detected_issues = []
        has_fill_problem = False

        if black_fill_percentage > self.config.black_fill_threshold:
            if self._has_uniform_color_fill(region_pixels, "black"):
                has_fill_problem = True
                detected_issues.append(
                    f"{region_name.title()} border has black fill: {black_fill_percentage*100:.1f}%"
                )

        return {
            "region": region_name,
            "black_percentage": black_fill_percentage,
            "is_problematic": has_fill_problem,
            "issues": detected_issues,
        }

    def _extract_region_pixels(
        self, grayscale_image: np.ndarray, region_name: str, height: int, width: int
    ) -> np.ndarray:
        if region_name == "top":
            region_height = int(height * self.config.top_region_percentage)
            return grayscale_image[:region_height, :]
        else:
            region_height = int(height * self.config.bottom_region_percentage)
            return grayscale_image[-region_height:, :]

    def _calculate_black_pixel_percentage(
        self, region_pixels: np.ndarray, total_pixel_count: int
    ) -> float:
        black_pixel_count = np.sum(region_pixels < self.config.black_threshold)
        return black_pixel_count / total_pixel_count

    def _calculate_white_pixel_percentage(
        self, region_pixels: np.ndarray, total_pixel_count: int
    ) -> float:
        white_pixel_count = np.sum(region_pixels > self.config.white_threshold)
        return white_pixel_count / total_pixel_count

    def _has_uniform_color_fill(
        self, region_pixels: np.ndarray, color_type: str
    ) -> bool:
        threshold = (
            self.config.black_threshold
            if color_type == "black"
            else self.config.white_threshold
        )

        if color_type == "black":
            matching_pixel_count = np.sum(region_pixels < threshold)
        else:
            matching_pixel_count = np.sum(region_pixels > threshold)

        uniformity_percentage = matching_pixel_count / region_pixels.size
        return uniformity_percentage >= self.config.uniformity_required

    def _calculate_confidence_score(self, problematic_region_count: int) -> float:
        total_region_count = self.config.check_top + self.config.check_bottom
        return (
            problematic_region_count / total_region_count
            if total_region_count > 0
            else 0.0
        )
