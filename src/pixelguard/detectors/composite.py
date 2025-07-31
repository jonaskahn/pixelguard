from typing import List

from .base import BaseDetector


class CompositeDetector(BaseDetector):
    """Combines multiple detectors into a single detector"""

    def __init__(self, detectors: List[BaseDetector]):
        super().__init__("composite")
        self.detectors = detectors

    def detect(self, image, image_path=""):
        """Run all detectors and aggregate results"""
        if not self.detectors:
            return self._create_result(False, 0.0, {}, [])

        results = []
        problematic_count = 0

        for detector in self.detectors:
            try:
                result = detector.detect(image, image_path)
                results.append(result)
                if result.is_problematic:
                    problematic_count += 1
            except Exception as e:
                error_result = detector._create_error_result(e, "detector_error")
                results.append(error_result)
                problematic_count += 1

        # Aggregate results
        is_problematic = problematic_count > 0
        confidence = problematic_count / len(self.detectors)

        # Combine details from all detectors
        details = {}
        all_issues = []

        for detector, result in zip(self.detectors, results):
            details[detector.name] = result.details
            if result.issues:
                all_issues.extend(result.issues)

        return self._create_result(is_problematic, confidence, details, all_issues)

    def add_detector(self, detector: BaseDetector):
        """Add a new detector to the composite"""
        self.detectors.append(detector)

    def remove_detector(self, name: str):
        """Remove a detector by name"""
        self.detectors = [
            detector for detector in self.detectors if detector.name != name
        ]

    def get_detector(self, name: str):
        """Get a detector by name"""
        for detector in self.detectors:
            if detector.name == name:
                return detector
        return None
