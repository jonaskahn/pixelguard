from src.pixelguard.analyzers.image import ImageAnalyzer
from src.pixelguard.core.config import DetectionConfig
from src.pixelguard.core.models import BatchReport, BatchSummary
from src.pixelguard.utils.file_finder import FileFinder


class BatchAnalyzer:

    def __init__(
        self,
        config: DetectionConfig,
        image_analyzer: ImageAnalyzer=None,
        file_finder: FileFinder=None,
    ):
        self.config = config
        self.image_analyzer = image_analyzer or ImageAnalyzer(config)
        self.file_finder = file_finder or FileFinder()

    def process(self, folder_path):
        discovered_image_paths = self.file_finder.find_images(folder_path, recursive=True)
        image_analyses = self._analyze_all_images(discovered_image_paths)
        batch_summary = self._create_batch_summary(image_analyses)

        return BatchReport(summary=batch_summary, analyses=image_analyses)

    def _analyze_all_images(self, image_paths):
        completed_analyses = []

        for current_index, image_path in enumerate(image_paths):
            single_analysis = self._analyze_single_image(image_path)
            completed_analyses.append(single_analysis)
            self._update_progress(current_index + 1, len(image_paths))

        return completed_analyses

    def _analyze_single_image(self, image_path):
        return self.image_analyzer.analyze(image_path)

    def _update_progress(self, current_count, total_count):
        pass

    def _create_batch_summary(self, image_analyses):
        problematic_image_count = sum(1 for analysis in image_analyses if analysis.is_problematic)
        total_image_count = len(image_analyses)

        return BatchSummary(
            total_images=total_image_count,
            problematic_images=problematic_image_count,
            passed_images=total_image_count - problematic_image_count,
        )
