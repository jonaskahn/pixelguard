from typing import List

from .base import BaseDetector
from ..core.config import RatioConfig


class RatioDetector(BaseDetector):
    def __init__(self, config: RatioConfig):
        super().__init__("ratio", config)
        self.config: RatioConfig = config

    def detect(self, image, image_path=""):
        """Detect aspect ratio and dimension issues in image"""
        if not self._validate_image(image):
            return self._create_error_result(
                ValueError("Invalid image provided"), "invalid_image"
            )

        try:
            height, width = image.shape[:2]
            current_ratio = width / height

            issues = []
            details = self._build_analysis_details(width, height, current_ratio)

            dimension_issues = self._check_dimension_constraints(width, height)
            issues.extend(dimension_issues)

            ratio_issues = self._check_aspect_ratio_compliance(current_ratio)
            issues.extend(ratio_issues)

            is_problematic = len(issues) > 0
            confidence = self._calculate_confidence_score(issues)

            details["ratio_issues"] = ratio_issues
            details["dimension_issues"] = dimension_issues

            return self._create_result(is_problematic, confidence, details, issues)

        except Exception as e:
            return self._create_error_result(e, "ratio_detection_error")

    def _build_analysis_details(
        self, width: int, height: int, current_ratio: float
    ) -> dict:
        """Build analysis details dictionary"""
        return {
            "width": width,
            "height": height,
            "current_ratio": current_ratio,
            "target_ratios": self.config.target_ratios,
            "tolerance": self.config.tolerance,
        }

    def _check_dimension_constraints(self, width: int, height: int) -> List[str]:
        """Check minimum and maximum dimension constraints"""
        issues = []

        if self.config.check_minimum_dimensions:
            minimum_issues = self._check_minimum_dimensions(width, height)
            issues.extend(minimum_issues)

        if self.config.check_maximum_dimensions:
            maximum_issues = self._check_maximum_dimensions(width, height)
            issues.extend(maximum_issues)

        return issues

    def _check_minimum_dimensions(self, width: int, height: int) -> List[str]:
        """Check if dimensions meet minimum requirements"""
        issues = []

        if width < self.config.minimum_width:
            issues.append(f"Width {width} is below minimum {self.config.minimum_width}")
        if height < self.config.minimum_height:
            issues.append(
                f"Height {height} is below minimum {self.config.minimum_height}"
            )

        return issues

    def _check_maximum_dimensions(self, width: int, height: int) -> List[str]:
        """Check if dimensions meet maximum requirements"""
        issues = []

        if width > self.config.maximum_width:
            issues.append(f"Width {width} exceeds maximum {self.config.maximum_width}")
        if height > self.config.maximum_height:
            issues.append(
                f"Height {height} exceeds maximum {self.config.maximum_height}"
            )

        return issues

    def _check_aspect_ratio_compliance(self, current_ratio: float) -> List[str]:
        """Check if current ratio matches any target ratios within tolerance"""
        issues = []
        closest_ratio = self._find_closest_target_ratio(current_ratio)

        if closest_ratio is None:
            issues.append(f"Ratio {current_ratio:.3f} doesn't match any target ratios")
        elif not self._is_ratio_within_tolerance(
            current_ratio, closest_ratio[0] / closest_ratio[1]
        ):
            target_ratio = closest_ratio[0] / closest_ratio[1]
            issues.append(
                f"Ratio {current_ratio:.3f} doesn't match any target ratios. "
                f"Closest: {target_ratio:.3f} ({closest_ratio[0]}:{closest_ratio[1]})"
            )

        return issues

    def _find_closest_target_ratio(self, current_ratio: float) -> tuple:
        """Find the closest target ratio to the current ratio"""
        if not self.config.target_ratios:
            return None

        closest_ratio = None
        min_difference = float("inf")

        for target_width, target_height in self.config.target_ratios:
            target_ratio = target_width / target_height
            difference = abs(current_ratio - target_ratio)

            if difference <= self.config.tolerance:
                return (target_width, target_height)  # Found exact match

            if difference < min_difference:
                min_difference = difference
                closest_ratio = (target_width, target_height)

        return closest_ratio

    def _is_ratio_within_tolerance(
        self, current_ratio: float, target_ratio: float
    ) -> bool:
        """Check if current ratio is within tolerance of target ratio"""
        return abs(current_ratio - target_ratio) <= self.config.tolerance

    def _calculate_confidence_score(self, issues: List[str]) -> float:
        """Calculate confidence score based on number of issues"""
        max_possible_issues = (
            len(self.config.target_ratios) + 2
        )  # +2 for min/max dimension checks
        return len(issues) / max(max_possible_issues, 1)
