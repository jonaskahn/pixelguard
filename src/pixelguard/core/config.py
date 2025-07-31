import os
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple


class DetectionMode(Enum):
    STRICT = "strict"
    DEFAULT = "default"
    LENIENT = "lenient"
    PHOTO = "photo"
    DOCUMENT = "document"
    CUSTOM = "custom"


@dataclass(frozen=True)
class BorderFillConfig:
    top_region_percentage: float = 0.1
    bottom_region_percentage: float = 0.1
    black_threshold: int = 1
    white_threshold: int = 255
    black_fill_threshold: float = 0.05
    white_fill_threshold: float = 0.05
    check_top: bool = False
    check_bottom: bool = True
    uniformity_required: float = 0.90


@dataclass(frozen=True)
class UniformColorConfig:
    color_delta_threshold: int = 15
    color_space: str = "LAB"
    uniform_coverage_threshold: float = 0.85
    sample_size: int = 1000
    ignore_edges: bool = True
    edge_ignore_percentage: float = 0.02


@dataclass(frozen=True)
class BackgroundDetectionConfig:
    detection_method: str = "edge_based"
    corner_sample_percentage: float = 0.08
    edge_sample_percentage: float = 0.05
    background_coverage_threshold: float = 0.65
    background_color_tolerance: int = 25
    histogram_bins: int = 64
    dominant_color_threshold: float = 0.60


@dataclass(frozen=True)
class RatioConfig:
    enabled: bool = True
    target_ratios: List[Tuple[float, float]] = field(
        default_factory=lambda: [(16, 9), (4, 3), (1, 1), (3, 4), (9, 16)]
    )
    tolerance: float = 0.1
    check_minimum_dimensions: bool = True
    minimum_width: int = 100
    minimum_height: int = 100
    check_maximum_dimensions: bool = False
    maximum_width: int = 10000
    maximum_height: int = 10000


@dataclass(frozen=True)
class DetectionConfig:
    border_fill: BorderFillConfig = field(default_factory=BorderFillConfig)
    uniform_color: UniformColorConfig = field(default_factory=UniformColorConfig)
    background: BackgroundDetectionConfig = field(
        default_factory=BackgroundDetectionConfig
    )
    ratio: RatioConfig = field(default_factory=RatioConfig)
    enabled_detectors: List[str] = field(
        default_factory=lambda: ["border_fill", "uniform_color", "background", "ratio"]
    )


@dataclass
class AnalysisConfig:
    mode: DetectionMode = DetectionMode.DEFAULT
    detection: DetectionConfig = field(default_factory=DetectionConfig)


class ConfigFactory:
    """Factory for creating detection configurations from different sources"""

    @staticmethod
    def from_mode(mode: DetectionMode) -> DetectionConfig:
        """Create configuration from predefined detection mode"""
        config_creators = {
            DetectionMode.STRICT: ConfigFactory._create_strict_config,
            DetectionMode.LENIENT: ConfigFactory._create_lenient_config,
            DetectionMode.PHOTO: ConfigFactory._create_photo_config,
            DetectionMode.DOCUMENT: ConfigFactory._create_document_config,
            DetectionMode.CUSTOM: ConfigFactory._create_custom_config,
        }

        creator = config_creators.get(mode, lambda: DetectionConfig())
        return creator()

    @staticmethod
    def _get_environment_value(key: str, default: str, converter=str) -> str:
        """Get environment variable value with type conversion"""
        value = os.getenv(key)
        return converter(value) if value is not None else converter(default)

    @staticmethod
    def _get_environment_float(key: str, default: float) -> float:
        """Get float value from environment variable"""
        return ConfigFactory._get_environment_value(key, str(default), float)

    @staticmethod
    def _get_environment_int(key: str, default: int) -> int:
        """Get int value from environment variable"""
        return ConfigFactory._get_environment_value(key, str(default), int)

    @staticmethod
    def _get_environment_bool(key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    @staticmethod
    def _get_environment_string(key: str, default: str) -> str:
        """Get string value from environment variable"""
        return os.getenv(key, default)

    @staticmethod
    def _get_environment_ratios(
        key: str, default: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """Get ratio list from environment variable (format: '16:9,4:3,1:1')"""
        value = os.getenv(key)
        if value is None:
            return default

        ratios = []
        for ratio_str in value.split(","):
            try:
                width, height = map(float, ratio_str.strip().split(":"))
                ratios.append((width, height))
            except (ValueError, AttributeError):
                continue
        return ratios if ratios else default

    @staticmethod
    def _get_custom_enabled_detectors() -> List[str]:
        """Get enabled detectors based on individual detector environment variables"""
        detector_enable_flags = {
            "border_fill": "PXG_DETECTOR_BORDER_FILL_ENABLED",
            "uniform_color": "PXG_DETECTOR_UNIFORM_COLOR_ENABLED",
            "background": "PXG_DETECTOR_BACKGROUND_ENABLED",
            "ratio": "PXG_DETECTOR_RATIO_ENABLED",
        }

        enabled_detectors = []
        for detector_name, env_key in detector_enable_flags.items():
            if ConfigFactory._get_environment_bool(env_key, True):
                enabled_detectors.append(detector_name)

        return enabled_detectors

    @staticmethod
    def _create_custom_config() -> DetectionConfig:
        """Create configuration from environment variables with PXG_ prefix"""
        return DetectionConfig(
            border_fill=ConfigFactory._create_border_fill_config_from_env(),
            uniform_color=ConfigFactory._create_uniform_color_config_from_env(),
            background=ConfigFactory._create_background_config_from_env(),
            ratio=ConfigFactory._create_ratio_config_from_env(),
            enabled_detectors=ConfigFactory._get_custom_enabled_detectors(),
        )

    @staticmethod
    def _create_border_fill_config_from_env() -> BorderFillConfig:
        """Create border fill configuration from environment variables"""
        return BorderFillConfig(
            top_region_percentage=ConfigFactory._get_environment_float(
                "PXG_BORDER_FILL_TOP_REGION_PERCENTAGE", 0.1
            ),
            bottom_region_percentage=ConfigFactory._get_environment_float(
                "PXG_BORDER_FILL_BOTTOM_REGION_PERCENTAGE", 0.1
            ),
            black_threshold=ConfigFactory._get_environment_int(
                "PXG_BORDER_FILL_BLACK_THRESHOLD", 30
            ),
            white_threshold=ConfigFactory._get_environment_int(
                "PXG_BORDER_FILL_WHITE_THRESHOLD", 225
            ),
            black_fill_threshold=ConfigFactory._get_environment_float(
                "PXG_BORDER_FILL_BLACK_FILL_THRESHOLD", 0.05
            ),
            white_fill_threshold=ConfigFactory._get_environment_float(
                "PXG_BORDER_FILL_WHITE_FILL_THRESHOLD", 0.05
            ),
            check_top=ConfigFactory._get_environment_bool(
                "PXG_BORDER_FILL_CHECK_TOP", False
            ),
            check_bottom=ConfigFactory._get_environment_bool(
                "PXG_BORDER_FILL_CHECK_BOTTOM", True
            ),
            uniformity_required=ConfigFactory._get_environment_float(
                "PXG_BORDER_FILL_UNIFORMITY_REQUIRED", 0.90
            ),
        )

    @staticmethod
    def _create_uniform_color_config_from_env() -> UniformColorConfig:
        """Create uniform color configuration from environment variables"""
        return UniformColorConfig(
            color_delta_threshold=ConfigFactory._get_environment_int(
                "PXG_UNIFORM_COLOR_DELTA_THRESHOLD", 15
            ),
            color_space=ConfigFactory._get_environment_string(
                "PXG_UNIFORM_COLOR_SPACE", "LAB"
            ),
            uniform_coverage_threshold=ConfigFactory._get_environment_float(
                "PXG_UNIFORM_COLOR_COVERAGE_THRESHOLD", 0.85
            ),
            sample_size=ConfigFactory._get_environment_int(
                "PXG_UNIFORM_COLOR_SAMPLE_SIZE", 1000
            ),
            ignore_edges=ConfigFactory._get_environment_bool(
                "PXG_UNIFORM_COLOR_IGNORE_EDGES", True
            ),
            edge_ignore_percentage=ConfigFactory._get_environment_float(
                "PXG_UNIFORM_COLOR_EDGE_IGNORE_PERCENTAGE", 0.02
            ),
        )

    @staticmethod
    def _create_background_config_from_env() -> BackgroundDetectionConfig:
        """Create background detection configuration from environment variables"""
        return BackgroundDetectionConfig(
            detection_method=ConfigFactory._get_environment_string(
                "PXG_BACKGROUND_DETECTION_METHOD", "edge_based"
            ),
            corner_sample_percentage=ConfigFactory._get_environment_float(
                "PXG_BACKGROUND_CORNER_SAMPLE_PERCENTAGE", 0.08
            ),
            edge_sample_percentage=ConfigFactory._get_environment_float(
                "PXG_BACKGROUND_EDGE_SAMPLE_PERCENTAGE", 0.05
            ),
            background_coverage_threshold=ConfigFactory._get_environment_float(
                "PXG_BACKGROUND_COVERAGE_THRESHOLD", 0.65
            ),
            background_color_tolerance=ConfigFactory._get_environment_int(
                "PXG_BACKGROUND_COLOR_TOLERANCE", 25
            ),
            histogram_bins=ConfigFactory._get_environment_int(
                "PXG_BACKGROUND_HISTOGRAM_BINS", 64
            ),
            dominant_color_threshold=ConfigFactory._get_environment_float(
                "PXG_BACKGROUND_DOMINANT_COLOR_THRESHOLD", 0.60
            ),
        )

    @staticmethod
    def _create_ratio_config_from_env() -> RatioConfig:
        """Create ratio configuration from environment variables"""
        return RatioConfig(
            enabled=ConfigFactory._get_environment_bool("PXG_RATIO_ENABLED", True),
            target_ratios=ConfigFactory._get_environment_ratios(
                "PXG_RATIO_TARGET_RATIOS",
                [(16, 9), (4, 3), (1, 1), (3, 4), (9, 16)],
            ),
            tolerance=ConfigFactory._get_environment_float("PXG_RATIO_TOLERANCE", 0.1),
            check_minimum_dimensions=ConfigFactory._get_environment_bool(
                "PXG_RATIO_CHECK_MINIMUM_DIMENSIONS", True
            ),
            minimum_width=ConfigFactory._get_environment_int(
                "PXG_RATIO_MINIMUM_WIDTH", 100
            ),
            minimum_height=ConfigFactory._get_environment_int(
                "PXG_RATIO_MINIMUM_HEIGHT", 100
            ),
            check_maximum_dimensions=ConfigFactory._get_environment_bool(
                "PXG_RATIO_CHECK_MAXIMUM_DIMENSIONS", False
            ),
            maximum_width=ConfigFactory._get_environment_int(
                "PXG_RATIO_MAXIMUM_WIDTH", 10000
            ),
            maximum_height=ConfigFactory._get_environment_int(
                "PXG_RATIO_MAXIMUM_HEIGHT", 10000
            ),
        )

    @staticmethod
    def _create_strict_config() -> DetectionConfig:
        """Create strict detection configuration"""
        return DetectionConfig(
            border_fill=BorderFillConfig(
                black_fill_threshold=0.03,
                white_fill_threshold=0.03,
                uniformity_required=0.95,
            ),
            uniform_color=UniformColorConfig(
                color_delta_threshold=10,
                uniform_coverage_threshold=0.80,
            ),
            background=BackgroundDetectionConfig(
                background_coverage_threshold=0.65,
                background_color_tolerance=15,
            ),
            ratio=RatioConfig(
                tolerance=0.05,
                target_ratios=[(16, 9), (4, 3), (1, 1)],
                minimum_width=200,
                minimum_height=200,
            ),
        )

    @staticmethod
    def _create_lenient_config() -> DetectionConfig:
        """Create lenient detection configuration"""
        return DetectionConfig(
            border_fill=BorderFillConfig(
                black_fill_threshold=0.15,
                white_fill_threshold=0.15,
                uniformity_required=0.80,
            ),
            uniform_color=UniformColorConfig(
                color_delta_threshold=30,
                uniform_coverage_threshold=0.95,
            ),
            background=BackgroundDetectionConfig(
                background_coverage_threshold=0.85,
                background_color_tolerance=35,
            ),
            ratio=RatioConfig(
                tolerance=0.2,
                target_ratios=[(16, 9), (4, 3), (1, 1), (3, 4), (9, 16), (21, 9)],
                minimum_width=50,
                minimum_height=50,
            ),
        )

    @staticmethod
    def _create_photo_config() -> DetectionConfig:
        """Create photo-optimized detection configuration"""
        return DetectionConfig(
            border_fill=BorderFillConfig(
                top_region_percentage=0.05,
                bottom_region_percentage=0.05,
                black_fill_threshold=0.08,
                white_fill_threshold=0.12,
                uniformity_required=0.85,
            ),
            uniform_color=UniformColorConfig(
                color_space="LAB",
                color_delta_threshold=20,
                uniform_coverage_threshold=0.90,
                ignore_edges=True,
            ),
            background=BackgroundDetectionConfig(
                detection_method="edge_based",
                background_coverage_threshold=0.75,
                background_color_tolerance=25,
            ),
            ratio=RatioConfig(
                tolerance=0.1,
                target_ratios=[(16, 9), (4, 3), (1, 1), (3, 4), (9, 16)],
                minimum_width=300,
                minimum_height=300,
            ),
        )

    @staticmethod
    def _create_document_config() -> DetectionConfig:
        """Create document-optimized detection configuration"""
        return DetectionConfig(
            border_fill=BorderFillConfig(
                black_fill_threshold=0.02,
                white_fill_threshold=0.30,
                uniformity_required=0.95,
            ),
            uniform_color=UniformColorConfig(
                color_space="RGB",
                color_delta_threshold=25,
                uniform_coverage_threshold=0.95,
                ignore_edges=False,
            ),
            background=BackgroundDetectionConfig(
                detection_method="histogram",
                background_coverage_threshold=0.80,
                background_color_tolerance=30,
            ),
            ratio=RatioConfig(
                tolerance=0.05,
                target_ratios=[(4, 3), (1, 1), (3, 4), (1.414, 1)],
                minimum_width=500,
                minimum_height=500,
            ),
        )
