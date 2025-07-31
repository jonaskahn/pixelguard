from src.pixelguard.analyzers.image import ImageAnalyzer
from src.pixelguard.core.config import DetectionConfig
from src.pixelguard.core.models import BatchReport, BatchSummary
from src.pixelguard.utils.file_finder import FileFinder


class BatchAnalyzer:
    def __init__(
        self,
        config: DetectionConfig,
        image_analyzer: ImageAnalyzer = None,
        file_finder: FileFinder = None,
    ):
        self.config = config
        self.image_analyzer = image_analyzer or ImageAnalyzer(config)
        self.file_finder = file_finder or FileFinder()

    def process(self, folder_path):
        """Process all images in folder and generate batch report"""
        image_paths = self.file_finder.find_images(folder_path, recursive=True)
        analyses = self._analyze_all_images(image_paths)
        summary = self._create_batch_summary(analyses)

        return BatchReport(summary=summary, analyses=analyses)

    def _analyze_all_images(self, image_paths):
        """Analyze all images in the provided paths"""
        analyses = []

        for current_index, image_path in enumerate(image_paths):
            analysis = self._analyze_single_image(image_path)
            analyses.append(analysis)
            self._update_progress(current_index + 1, len(image_paths))

        return analyses

    def _analyze_single_image(self, image_path):
        """Analyze a single image"""
        return self.image_analyzer.analyze(image_path)

    def _update_progress(self, current, total):
        """Update progress indicator (can be overridden for custom progress reporting)"""
        pass

    def _create_batch_summary(self, analyses):
        """Create batch summary from analysis results"""
        problematic_count = sum(1 for analysis in analyses if analysis.is_problematic)
        total_count = len(analyses)

        return BatchSummary(
            total_images=total_count,
            problematic_images=problematic_count,
            passed_images=total_count - problematic_count,
        )
