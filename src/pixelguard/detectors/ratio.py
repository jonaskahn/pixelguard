from typing import List

from .base import BaseDetector
from ..core.config import RatioConfig


class RatioDetector(BaseDetector):

    def __init__(self, config: RatioConfig):
        super().__init__("ratio", config)
        self.config: RatioConfig = config

    def detect(self, image, image_path=""):
        if not self._validate_image(image):
            return self._create_error_result(
                ValueError("Invalid image provided"), "invalid_image"
            )

        try:
            height, width = image.shape[:2]
            actual_aspect_ratio = width / height

            detected_issues = []
            analysis_details = self._build_ratio_analysis_details(width, height, actual_aspect_ratio)

            dimension_violations = self._validate_dimension_constraints(width, height)
            detected_issues.extend(dimension_violations)

            aspect_ratio_violations = self._validate_aspect_ratio_compliance(actual_aspect_ratio)
            detected_issues.extend(aspect_ratio_violations)

            has_ratio_issues = len(detected_issues) > 0
            detection_confidence = self._calculate_confidence_score(detected_issues)

            analysis_details["aspect_ratio_violations"] = aspect_ratio_violations
            analysis_details["dimension_violations"] = dimension_violations

            return self._create_result(has_ratio_issues, detection_confidence, analysis_details, detected_issues)

        except Exception as e:
            return self._create_error_result(e, "ratio_detection_error")

    def _build_ratio_analysis_details(
        self, width: int, height: int, actual_aspect_ratio: float
    ) -> dict:
        return {
            "width": width,
            "height": height,
            "actual_aspect_ratio": actual_aspect_ratio,
            "target_ratios": self.config.target_ratios,
            "tolerance": self.config.tolerance,
        }

    def _validate_dimension_constraints(self, width: int, height: int) -> List[str]:
        violations = []

        if self.config.check_minimum_dimensions:
            minimum_violations = self._validate_minimum_dimensions(width, height)
            violations.extend(minimum_violations)

        if self.config.check_maximum_dimensions:
            maximum_violations = self._validate_maximum_dimensions(width, height)
            violations.extend(maximum_violations)

        return violations

    def _validate_minimum_dimensions(self, width: int, height: int) -> List[str]:
        violations = []

        if width < self.config.minimum_width:
            violations.append(f"Width {width} is below minimum {self.config.minimum_width}")
        if height < self.config.minimum_height:
            violations.append(
                f"Height {height} is below minimum {self.config.minimum_height}"
            )

        return violations

    def _validate_maximum_dimensions(self, width: int, height: int) -> List[str]:
        violations = []

        if width > self.config.maximum_width:
            violations.append(f"Width {width} exceeds maximum {self.config.maximum_width}")
        if height > self.config.maximum_height:
            violations.append(
                f"Height {height} exceeds maximum {self.config.maximum_height}"
            )

        return violations

    def _validate_aspect_ratio_compliance(self, actual_ratio: float) -> List[str]:
        violations = []
        closest_target_ratio = self._find_closest_target_ratio(actual_ratio)

        if closest_target_ratio is None:
            violations.append(f"Ratio {actual_ratio:.3f} doesn't match any target ratios")
        elif not self._is_ratio_within_tolerance(
            actual_ratio, closest_target_ratio[0] / closest_target_ratio[1]
        ):
            target_ratio_value = closest_target_ratio[0] / closest_target_ratio[1]
            violations.append(
                f"Ratio {actual_ratio:.3f} doesn't match any target ratios. "
                f"Closest: {target_ratio_value:.3f} ({closest_target_ratio[0]}:{closest_target_ratio[1]})"
            )

        return violations

    def _find_closest_target_ratio(self, actual_ratio: float) -> tuple:
        if not self.config.target_ratios:
            return None

        closest_ratio_tuple = None
        smallest_difference = float("inf")

        for target_width, target_height in self.config.target_ratios:
            target_ratio_value = target_width / target_height
            difference = abs(actual_ratio - target_ratio_value)

            if difference <= self.config.tolerance:
                return (target_width, target_height)

            if difference < smallest_difference:
                smallest_difference = difference
                closest_ratio_tuple = (target_width, target_height)

        return closest_ratio_tuple

    def _is_ratio_within_tolerance(
        self, actual_ratio: float, target_ratio_value: float
    ) -> bool:
        return abs(actual_ratio - target_ratio_value) <= self.config.tolerance

    def _calculate_confidence_score(self, detected_issues: List[str]) -> float:
        max_possible_issue_count = (
            len(self.config.target_ratios) + 2
        )
        return len(detected_issues) / max(max_possible_issue_count, 1)
