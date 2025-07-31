from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class DetectionResult:
    detector_name: str
    is_problematic: bool
    confidence: float
    details: dict = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


@dataclass
class ImageAnalysis:
    file_path: Path
    width: int
    height: int
    detection_results: List[DetectionResult] = field(default_factory=list)
    is_problematic: bool = False

    def add_detection_result(self, detection_result: DetectionResult):
        self.detection_results.append(detection_result)
        if detection_result.is_problematic:
            self.is_problematic = True


@dataclass
class BatchSummary:
    total_images: int
    problematic_images: int
    passed_images: int


@dataclass
class BatchReport:
    summary: BatchSummary
    analyses: List[ImageAnalysis] = field(default_factory=list)
