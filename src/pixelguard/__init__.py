from src.pixelguard.analyzers.batch import BatchAnalyzer
from src.pixelguard.analyzers.image import ImageAnalyzer
from src.pixelguard.core.config import ConfigFactory, DetectionMode, DetectionConfig


class PixelGuard:
    """Main interface for PixelGuard image quality analysis"""

    def __init__(self, config: DetectionConfig = None, mode: str = None):
        self.config = PixelGuard._initialize_config(config, mode)
        self._initialize_analyzers()

    @staticmethod
    def _initialize_config(config: DetectionConfig, mode: str) -> DetectionConfig:
        """Initialize configuration from provided config or mode"""
        if config is not None:
            return config
        elif mode is not None:
            return ConfigFactory.from_mode(DetectionMode(mode))
        else:
            return ConfigFactory.from_mode(DetectionMode.DEFAULT)

    def _initialize_analyzers(self):
        self.image_analyzer = ImageAnalyzer(self.config)
        self.batch_analyzer = BatchAnalyzer(
            self.config, image_analyzer=self.image_analyzer
        )

    def analyze_image(self, image_path):
        """Analyze a single image for quality issues"""
        return self.image_analyzer.analyze(image_path)

    def analyze_batch(self, folder_path):
        """Analyze all images in a folder for quality issues"""
        return self.batch_analyzer.process(folder_path)


__all__ = [
    "PixelGuard",
    "ConfigFactory",
    "DetectionMode",
]
