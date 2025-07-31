from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.pixelguard.core.config import (
    BorderFillConfig,
    UniformColorConfig,
    BackgroundDetectionConfig,
)
from src.pixelguard.core.models import DetectionResult
from src.pixelguard.detectors.background import BackgroundDetector
from src.pixelguard.detectors.base import BaseDetector
from src.pixelguard.detectors.border_fill import BorderFillDetector
from src.pixelguard.detectors.composite import CompositeDetector
from src.pixelguard.detectors.uniform_color import UniformColorDetector


class ConcreteTestDetector(BaseDetector):
    """Concrete implementation of BaseDetector for testing."""

    def detect(self, image, image_path=""):
        return self._create_result(False, 0.5, {}, [])


class TestBaseDetector:
    """Test suite for the BaseDetector abstract class."""

    def test_base_detector_initialization(self):
        """Given a detector name and config, When BaseDetector is initialized, Then it should set the attributes correctly."""
        # Given
        name = "test_detector"
        config = Mock()

        # When
        detector = ConcreteTestDetector(name, config)

        # Then
        assert detector.name == name
        assert detector.config == config

    def test_create_result_with_valid_parameters(self):
        """Given valid result parameters, When _create_result is called, Then it should return a DetectionResult."""
        # Given
        detector = ConcreteTestDetector("test_detector")
        is_problematic = True
        confidence = 0.85
        details = {"test": "value"}
        issues = ["Test issue"]

        # When
        result = detector._create_result(is_problematic, confidence, details, issues)

        # Then
        assert isinstance(result, DetectionResult)
        assert result.detector_name == "test_detector"
        assert result.is_problematic == is_problematic
        assert result.confidence == confidence
        assert result.details == details
        assert result.issues == issues

    def test_create_result_with_confidence_clamping(self):
        """Given confidence values outside [0,1], When _create_result is called, Then it should clamp the confidence."""
        # Given
        detector = ConcreteTestDetector("test_detector")

        # When
        result_high = detector._create_result(True, 1.5, {}, [])
        result_low = detector._create_result(True, -0.5, {}, [])

        # Then
        assert result_high.confidence == 1.0
        assert result_low.confidence == 0.0

    def test_create_result_with_default_values(self):
        """Given minimal parameters, When _create_result is called, Then it should use default values."""
        # Given
        detector = ConcreteTestDetector("test_detector")

        # When
        result = detector._create_result(False, 0.5)

        # Then
        assert result.details == {}
        assert result.issues == []

    def test_create_error_result(self):
        """Given an exception, When _create_error_result is called, Then it should return an error result."""
        # Given
        detector = ConcreteTestDetector("test_detector")
        error = ValueError("Test error")

        # When
        result = detector._create_error_result(error, "test_error")

        # Then
        assert result.is_problematic is True
        assert result.confidence == 1.0
        assert result.details["error_type"] == "test_error"
        assert result.details["error_message"] == "Test error"
        assert "test_detector detection failed: Test error" in result.issues[0]

    def test_validate_image_with_valid_image(self):
        """Given a valid numpy image, When _validate_image is called, Then it should return True."""
        # Given
        detector = ConcreteTestDetector("test_detector")
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        # When
        is_valid = detector._validate_image(image)

        # Then
        assert is_valid is True

    def test_validate_image_with_invalid_images(self):
        """Given invalid images, When _validate_image is called, Then it should return False."""
        # Given
        detector = ConcreteTestDetector("test_detector")

        # When & Then
        assert detector._validate_image(None) is False
        assert detector._validate_image("not_an_image") is False
        assert detector._validate_image(np.zeros(10)) is False  # 1D array


class TestBorderFillDetector:
    """Test suite for the BorderFillDetector."""

    @pytest.fixture
    def border_config(self):
        """Create a border fill configuration for testing."""
        return BorderFillConfig(
            top_region_percentage=0.1,
            bottom_region_percentage=0.1,
            black_threshold=30,
            white_threshold=225,
            black_fill_threshold=0.05,
            white_fill_threshold=0.05,
            check_top=True,
            check_bottom=True,
            uniformity_required=0.90,
        )

    @pytest.fixture
    def detector(self, border_config):
        """Create a BorderFillDetector instance."""
        return BorderFillDetector(border_config)

    def test_border_fill_detector_initialization(self, border_config):
        """Given a BorderFillConfig, When BorderFillDetector is initialized, Then it should set up correctly."""
        # Given
        config = border_config

        # When
        detector = BorderFillDetector(config)

        # Then
        assert detector.name == "border_fill"
        assert detector.config == config

    def test_detect_with_valid_image_no_borders(self, detector):
        """Given a valid image without borders, When detect is called, Then it should return non-problematic result."""
        # Given
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Gray image

        # When
        result = detector.detect(image)

        # Then
        assert result.is_problematic is False
        assert result.detector_name == "border_fill"
        assert "top_border" in result.details
        assert "bottom_border" in result.details

    def test_detect_with_black_top_border(self, detector):
        """Given an image with black top border, When detect is called, Then it should detect the problematic border."""
        # Given
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        # Add black top border
        image[:10, :] = 0

        # When
        result = detector.detect(image)

        # Then
        assert result.is_problematic is True
        assert "Top border has black fill" in " ".join(result.issues)

    def test_detect_with_white_bottom_border(self, detector):
        """Given an image with white bottom border, When detect is called, Then it should detect the problematic border."""
        # Given
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        # Add white bottom border
        image[-10:, :] = 255

        # When
        result = detector.detect(image)

        # Then
        assert result.is_problematic is True
        assert "Bottom border has white fill" in " ".join(result.issues)

    def test_detect_with_invalid_image(self, detector):
        """Given an invalid image, When detect is called, Then it should return an error result."""
        # Given
        invalid_image = None

        # When
        result = detector.detect(invalid_image)

        # Then
        assert result.is_problematic is True
        assert result.details["error_type"] == "invalid_image"

    def test_detect_with_exception(self, detector):
        """Given an image that causes an exception, When detect is called, Then it should return an error result."""
        # Given
        image = np.ones((100, 100, 3), dtype=np.uint8)

        # When
        with patch.object(
            detector, "_convert_to_grayscale", side_effect=Exception("Test error")
        ):
            result = detector.detect(image)

        # Then
        assert result.is_problematic is True
        assert result.details["error_type"] == "border_fill_error"

    def test_analyze_border_region_top(self, detector):
        """Given a top border region, When _analyze_border_region is called, Then it should analyze correctly."""
        # Given
        gray = np.ones((100, 100), dtype=np.uint8) * 128
        gray[:10, :] = 0  # Black top border

        # When
        result = detector._analyze_border_region(gray, "top", 100, 100)

        # Then
        assert result["region"] == "top"
        assert result["black_percentage"] > 0
        assert result["white_percentage"] == 0

    def test_analyze_border_region_bottom(self, detector):
        """Given a bottom border region, When _analyze_border_region is called, Then it should analyze correctly."""
        # Given
        gray = np.ones((100, 100), dtype=np.uint8) * 128
        gray[-10:, :] = 255  # White bottom border

        # When
        result = detector._analyze_border_region(gray, "bottom", 100, 100)

        # Then
        assert result["region"] == "bottom"
        assert result["white_percentage"] > 0
        assert result["black_percentage"] == 0


class TestUniformColorDetector:
    """Test suite for the UniformColorDetector."""

    @pytest.fixture
    def uniform_config(self):
        """Create a uniform color configuration for testing."""
        return UniformColorConfig(
            color_delta_threshold=15,
            color_space="LAB",
            uniform_coverage_threshold=0.85,
            sample_size=1000,
            ignore_edges=True,
            edge_ignore_percentage=0.02,
        )

    @pytest.fixture
    def detector(self, uniform_config):
        """Create a UniformColorDetector instance."""
        return UniformColorDetector(uniform_config)

    def test_uniform_color_detector_initialization(self, uniform_config):
        """Given a UniformColorConfig, When UniformColorDetector is initialized, Then it should set up correctly."""
        # Given
        config = uniform_config

        # When
        detector = UniformColorDetector(config)

        # Then
        assert detector.name == "uniform_color"
        assert detector.config == config

    def test_detect_with_varied_image(self, detector):
        """Given a varied color image, When detect is called, Then it should return non-problematic result."""
        # Given
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # When
        result = detector.detect(image)

        # Then
        assert result.detector_name == "uniform_color"
        assert "dominant_color" in result.details
        assert "uniformity_percentage" in result.details

    def test_detect_with_uniform_image(self, detector):
        """Given a uniform color image, When detect is called, Then it should detect the problematic uniformity."""
        # Given
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Uniform gray

        # When
        result = detector.detect(image)

        # Then
        assert bool(result.is_problematic) is True
        assert "uniform color" in " ".join(result.issues)

    def test_detect_with_invalid_image(self, detector):
        """Given an invalid image, When detect is called, Then it should return an error result."""
        # Given
        invalid_image = None

        # When
        result = detector.detect(invalid_image)

        # Then
        assert result.is_problematic is True
        assert result.details["error_type"] == "invalid_image"

    def test_convert_to_color_space_lab(self, detector):
        """Given an image, When _convert_to_color_space is called with LAB, Then it should convert correctly."""
        # Given
        image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

        # When
        with patch("cv2.cvtColor") as mock_cvt:
            detector._convert_to_color_space(image)

        # Then
        mock_cvt.assert_called_once_with(image, 44)  # cv2.COLOR_BGR2LAB

    def test_convert_to_color_space_hsv(self):
        """Given an image, When _convert_to_color_space is called with HSV, Then it should convert correctly."""
        # Given
        config = UniformColorConfig(
            color_delta_threshold=15,
            color_space="HSV",
            uniform_coverage_threshold=0.85,
            sample_size=1000,
            ignore_edges=True,
            edge_ignore_percentage=0.02,
        )
        detector = UniformColorDetector(config)
        image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

        # When
        with patch("cv2.cvtColor") as mock_cvt:
            detector._convert_to_color_space(image)

        # Then
        mock_cvt.assert_called_once_with(image, 40)  # cv2.COLOR_BGR2HSV

    def test_sample_pixels_with_edge_ignoring(self, detector):
        """Given an image with edge ignoring enabled, When _sample_pixels is called, Then it should ignore edges."""
        # Given
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # When
        pixels = detector._sample_pixels(image)

        # Then
        assert len(pixels.shape) == 2
        assert pixels.shape[1] == 3

    def test_sample_pixels_without_edge_ignoring(self):
        """Given an image without edge ignoring, When _sample_pixels is called, Then it should include all pixels."""
        # Given
        config = UniformColorConfig(
            color_delta_threshold=15,
            color_space="LAB",
            uniform_coverage_threshold=0.85,
            sample_size=1000,
            ignore_edges=False,
            edge_ignore_percentage=0.02,
        )
        detector = UniformColorDetector(config)
        image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

        # When
        pixels = detector._sample_pixels(image)

        # Then
        assert len(pixels.shape) == 2
        assert pixels.shape[1] == 3


class TestBackgroundDetector:
    """Test suite for the BackgroundDetector."""

    @pytest.fixture
    def background_config(self):
        """Create a background detection configuration for testing."""
        return BackgroundDetectionConfig(
            detection_method="edge_based",
            corner_sample_percentage=0.05,
            edge_sample_percentage=0.03,
            background_coverage_threshold=0.70,
            background_color_tolerance=20,
            histogram_bins=64,
            dominant_color_threshold=0.60,
        )

    @pytest.fixture
    def detector(self, background_config):
        """Create a BackgroundDetector instance."""
        return BackgroundDetector(background_config)

    def test_background_detector_initialization(self, background_config):
        """Given a BackgroundDetectionConfig, When BackgroundDetector is initialized, Then it should set up correctly."""
        # Given
        config = background_config

        # When
        detector = BackgroundDetector(config)

        # Then
        assert detector.name == "background"
        assert detector.config == config

    def test_detect_with_varied_image(self, detector):
        """Given a varied image, When detect is called, Then it should return non-problematic result."""
        # Given
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # When
        result = detector.detect(image)

        # Then
        assert result.detector_name == "background"
        assert "background_color" in result.details
        assert "background_coverage" in result.details

    def test_detect_with_background_dominant_image(self, detector):
        """Given a background dominant image, When detect is called, Then it should detect the problematic background."""
        # Given
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Uniform background
        # Add small object in center
        image[40:60, 40:60] = 255

        # When
        result = detector.detect(image)

        # Then
        assert bool(result.is_problematic) is True
        assert "Background dominates" in " ".join(result.issues)

    def test_detect_with_invalid_image(self, detector):
        """Given an invalid image, When detect is called, Then it should return an error result."""
        # Given
        invalid_image = None

        # When
        result = detector.detect(invalid_image)

        # Then
        assert result.is_problematic is True
        assert result.details["error_type"] == "invalid_image"

    def test_detect_background_color_edge_based(self, detector):
        """Given an image, When _detect_background_color is called with edge_based method, Then it should use edge sampling."""
        # Given
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # When
        with patch.object(detector, "_find_most_common_color") as mock_find:
            mock_find.return_value = np.array([128, 128, 128])
            color = detector._detect_background_color(image)

        # Then
        assert mock_find.called
        assert color.shape == (3,)

    def test_detect_background_color_corner_based(self):
        """Given an image, When _detect_background_color is called with corner_based method, Then it should use corner sampling."""
        # Given
        config = BackgroundDetectionConfig(
            detection_method="corner_based",
            corner_sample_percentage=0.05,
            edge_sample_percentage=0.03,
            background_coverage_threshold=0.70,
            background_color_tolerance=20,
            histogram_bins=64,
            dominant_color_threshold=0.60,
        )
        detector = BackgroundDetector(config)
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # When
        with patch.object(detector, "_find_most_common_color") as mock_find:
            mock_find.return_value = np.array([128, 128, 128])
            color = detector._detect_background_color(image)

        # Then
        assert mock_find.called
        assert color.shape == (3,)

    def test_detect_background_color_histogram_based(self):
        """Given an image, When _detect_background_color is called with histogram_based method, Then it should use histogram."""
        # Given
        config = BackgroundDetectionConfig(
            detection_method="histogram_based",
            corner_sample_percentage=0.05,
            edge_sample_percentage=0.03,
            background_coverage_threshold=0.70,
            background_color_tolerance=20,
            histogram_bins=64,
            dominant_color_threshold=0.60,
        )
        detector = BackgroundDetector(config)
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # When
        with patch("cv2.calcHist") as mock_hist:
            # Mock histogram to return proper 3D array structure
            mock_hist.return_value = np.array([[[1000]], [[100]], [[50]]])
            color = detector._detect_background_color(image)

        # Then
        assert mock_hist.called
        assert color.shape == (3,)


class TestCompositeDetector:
    """Test suite for the CompositeDetector."""

    @pytest.fixture
    def mock_detectors(self):
        """Create mock detectors for testing."""
        detector1 = Mock(spec=BaseDetector)
        detector1.name = "detector1"
        detector1.detect.return_value = Mock(
            is_problematic=False, details={}, issues=[]
        )

        detector2 = Mock(spec=BaseDetector)
        detector2.name = "detector2"
        detector2.detect.return_value = Mock(
            is_problematic=True, details={}, issues=["Issue 2"]
        )

        return [detector1, detector2]

    @pytest.fixture
    def composite_detector(self, mock_detectors):
        """Create a CompositeDetector instance."""
        return CompositeDetector(mock_detectors)

    def test_composite_detector_initialization(self, mock_detectors):
        """Given a list of detectors, When CompositeDetector is initialized, Then it should set up correctly."""
        # Given
        detectors = mock_detectors

        # When
        composite = CompositeDetector(detectors)

        # Then
        assert composite.name == "composite"
        assert composite.detectors == detectors

    def test_detect_with_multiple_detectors(self, composite_detector, mock_detectors):
        """Given multiple detectors, When detect is called, Then it should aggregate results."""
        # Given
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # When
        result = composite_detector.detect(image)

        # Then
        assert result.is_problematic is True
        assert result.confidence == 0.5  # 1 problematic out of 2 detectors
        assert len(result.details) == 2
        assert "Issue 2" in result.issues

    def test_detect_with_no_detectors(self):
        """Given no detectors, When detect is called, Then it should return non-problematic result."""
        # Given
        composite = CompositeDetector([])
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # When
        result = composite.detect(image)

        # Then
        assert result.is_problematic is False
        assert result.confidence == 0.0

    def test_detect_with_detector_exception(self, mock_detectors):
        """Given a detector that raises an exception, When detect is called, Then it should handle the error."""
        # Given
        detector = Mock(spec=BaseDetector)
        detector.name = "error_detector"
        detector.detect.side_effect = Exception("Test error")
        detector._create_error_result.return_value = Mock(
            is_problematic=True, details={}, issues=["Error"]
        )

        composite = CompositeDetector([detector])
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # When
        result = composite.detect(image)

        # Then
        assert result.is_problematic is True
        assert result.confidence == 1.0
        assert "Error" in result.issues

    def test_add_detector(self, composite_detector):
        """Given a new detector, When add_detector is called, Then it should add the detector."""
        # Given
        new_detector = Mock(spec=BaseDetector)
        new_detector.name = "new_detector"
        initial_count = len(composite_detector.detectors)

        # When
        composite_detector.add_detector(new_detector)

        # Then
        assert len(composite_detector.detectors) == initial_count + 1
        assert new_detector in composite_detector.detectors

    def test_remove_detector(self, composite_detector):
        """Given a detector name, When remove_detector is called, Then it should remove the detector."""
        # Given
        detector_name = "detector1"
        initial_count = len(composite_detector.detectors)

        # When
        composite_detector.remove_detector(detector_name)

        # Then
        assert len(composite_detector.detectors) == initial_count - 1
        assert not any(d.name == detector_name for d in composite_detector.detectors)

    def test_get_detector_existing(self, composite_detector):
        """Given an existing detector name, When get_detector is called, Then it should return the detector."""
        # Given
        detector_name = "detector1"

        # When
        detector = composite_detector.get_detector(detector_name)

        # Then
        assert detector is not None
        assert detector.name == detector_name

    def test_get_detector_nonexistent(self, composite_detector):
        """Given a non-existent detector name, When get_detector is called, Then it should return None."""
        # Given
        detector_name = "nonexistent"

        # When
        detector = composite_detector.get_detector(detector_name)

        # Then
        assert detector is None
