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
        """Detect border fill issues in image"""
        if not self._validate_image(image):
            return self._create_error_result(
                ValueError("Invalid image provided"), "invalid_image"
            )

        try:
            gray_image = self._convert_to_grayscale(image)
            height, width = gray_image.shape

            issues = []
            details = {}
            problematic_regions_count = 0

            if self.config.check_top:
                top_result = self._analyze_border_region(
                    gray_image, "top", height, width
                )
                details["top_border"] = top_result
                if top_result["is_problematic"]:
                    issues.extend(top_result["issues"])
                    problematic_regions_count += 1

            if self.config.check_bottom:
                bottom_result = self._analyze_border_region(
                    gray_image, "bottom", height, width
                )
                details["bottom_border"] = bottom_result
                if bottom_result["is_problematic"]:
                    issues.extend(bottom_result["issues"])
                    problematic_regions_count += 1

            is_problematic = len(issues) > 0
            confidence = self._calculate_confidence_score(problematic_regions_count)

            return self._create_result(is_problematic, confidence, details, issues)

        except Exception as e:
            return self._create_error_result(e, "border_fill_error")

    def _convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale for analysis"""
        return convert_to_grayscale(image)

    def _analyze_border_region(
        self, gray_image: np.ndarray, region: str, height: int, width: int
    ) -> Dict:
        """Analyze a specific border region for fill issues"""
        region_data = self._extract_region_data(gray_image, region, height, width)
        total_pixels = region_data.size

        black_percentage = self._calculate_black_pixel_percentage(
            region_data, total_pixels
        )
        white_percentage = self._calculate_white_pixel_percentage(
            region_data, total_pixels
        )

        issues = []
        is_problematic = False

        if black_percentage > self.config.black_fill_threshold:
            if self._is_uniform_region(region_data, "black"):
                is_problematic = True
                issues.append(
                    f"{region.title()} border has black fill: {black_percentage*100:.1f}%"
                )

        if white_percentage > self.config.white_fill_threshold:
            if self._is_uniform_region(region_data, "white"):
                is_problematic = True
                issues.append(
                    f"{region.title()} border has white fill: {white_percentage*100:.1f}%"
                )

        return {
            "region": region,
            "black_percentage": black_percentage,
            "white_percentage": white_percentage,
            "is_problematic": is_problematic,
            "issues": issues,
        }

    def _extract_region_data(
        self, gray_image: np.ndarray, region: str, height: int, width: int
    ) -> np.ndarray:
        """Extract pixel data from specified border region"""
        if region == "top":
            region_height = int(height * self.config.top_region_percentage)
            return gray_image[:region_height, :]
        else:
            region_height = int(height * self.config.bottom_region_percentage)
            return gray_image[-region_height:, :]

    def _calculate_black_pixel_percentage(
        self, region_data: np.ndarray, total_pixels: int
    ) -> float:
        """Calculate percentage of black pixels in region"""
        black_pixels = np.sum(region_data < self.config.black_threshold)
        return black_pixels / total_pixels

    def _calculate_white_pixel_percentage(
        self, region_data: np.ndarray, total_pixels: int
    ) -> float:
        """Calculate percentage of white pixels in region"""
        white_pixels = np.sum(region_data > self.config.white_threshold)
        return white_pixels / total_pixels

    def _is_uniform_region(self, region_data: np.ndarray, color_type: str) -> bool:
        """Check if region is uniform in specified color type"""
        threshold = (
            self.config.black_threshold
            if color_type == "black"
            else self.config.white_threshold
        )

        if color_type == "black":
            uniform_pixels = np.sum(region_data < threshold)
        else:
            uniform_pixels = np.sum(region_data > threshold)

        uniformity = uniform_pixels / region_data.size
        return uniformity >= self.config.uniformity_required

    def _calculate_confidence_score(self, problematic_regions_count: int) -> float:
        """Calculate confidence score based on problematic regions"""
        total_regions = self.config.check_top + self.config.check_bottom
        return problematic_regions_count / total_regions if total_regions > 0 else 0.0
