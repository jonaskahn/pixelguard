from src.pixelguard.core.config import DetectionConfig
from src.pixelguard.core.models import ImageAnalysis
from src.pixelguard.detectors.background import BackgroundDetector
from src.pixelguard.detectors.border_fill import BorderFillDetector
from src.pixelguard.detectors.composite import CompositeDetector
from src.pixelguard.detectors.ratio import RatioDetector
from src.pixelguard.detectors.uniform_color import UniformColorDetector
from src.pixelguard.utils.image_loader import ImageLoader


class ImageAnalyzer:
    def __init__(
        self,
        config: DetectionConfig,
        detector: CompositeDetector = None,
        image_loader: ImageLoader = None,
    ):
        self.config = config
        self.detector = detector or self._build_detector()
        self.image_loader = image_loader or ImageLoader()

    def _build_detector(self):
        """Build composite detector from enabled detectors"""
        detectors = []

        detector_builders = {
            "border_fill": lambda: BorderFillDetector(self.config.border_fill),
            "uniform_color": lambda: UniformColorDetector(self.config.uniform_color),
            "background": lambda: BackgroundDetector(self.config.background),
            "ratio": lambda: RatioDetector(self.config.ratio),
        }

        for detector_name in self.config.enabled_detectors:
            if detector_name in detector_builders:
                detectors.append(detector_builders[detector_name]())

        return CompositeDetector(detectors)

    def analyze(self, image_path):
        """Analyze a single image for quality issues"""
        image = self.image_loader.load(image_path)
        height, width = image.shape[:2]

        analysis = self._create_initial_analysis(image_path, width, height)
        detection_result = self.detector.detect(image, image_path)
        analysis.add_detection_result(detection_result)

        return analysis

    def _create_initial_analysis(
        self, image_path, width: int, height: int
    ) -> ImageAnalysis:
        """Create initial image analysis with basic information"""
        return ImageAnalysis(file_path=image_path, width=width, height=height)
