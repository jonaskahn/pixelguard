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
        detector: CompositeDetector=None,
        image_loader: ImageLoader=None,
    ):
        self.config = config
        self.detector = detector or self._build_detector()
        self.image_loader = image_loader or ImageLoader()

    def _build_detector(self):
        active_detectors = []

        detector_factory_map = {
            "border_fill": lambda: BorderFillDetector(self.config.border_fill),
            "uniform_color": lambda: UniformColorDetector(self.config.uniform_color),
            "background": lambda: BackgroundDetector(self.config.background),
            "ratio": lambda: RatioDetector(self.config.ratio),
        }

        for detector_name in self.config.enabled_detectors:
            if detector_name in detector_factory_map:
                active_detectors.append(detector_factory_map[detector_name]())

        return CompositeDetector(active_detectors)

    def analyze(self, image_path):
        loaded_image = self.image_loader.load(image_path)
        height, width = loaded_image.shape[:2]

        image_analysis = self._create_initial_analysis(image_path, width, height)
        composite_detection_result = self.detector.detect(loaded_image, image_path)
        image_analysis.add_detection_result(composite_detection_result)

        return image_analysis

    def _create_initial_analysis(
        self, image_path, width: int, height: int
    ) -> ImageAnalysis:
        return ImageAnalysis(file_path=image_path, width=width, height=height)
