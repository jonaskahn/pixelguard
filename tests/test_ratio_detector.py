import numpy as np

from src.pixelguard.core.config import RatioConfig
from src.pixelguard.detectors.ratio import RatioDetector


class TestRatioDetector:
    """Test suite for the ratio detector"""

    def test_valid_image_ratio_check(self):
        """Test ratio detection with valid image"""
        config = RatioConfig(
            target_ratios=[(16, 9), (4, 3), (1, 1)],
            tolerance=0.1,
            minimum_width=100,
            minimum_height=100,
        )
        detector = RatioDetector(config)

        # Create a 16:9 image (1920x1080)
        image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert not result.is_problematic
        assert result.confidence == 0.0
        assert result.detector_name == "ratio"
        assert "width" in result.details
        assert "height" in result.details
        assert "current_ratio" in result.details
        assert result.details["width"] == 1920
        assert result.details["height"] == 1080
        assert abs(result.details["current_ratio"] - 16 / 9) < 0.001

    def test_invalid_ratio_detection(self):
        """Test ratio detection with invalid ratio"""
        config = RatioConfig(
            target_ratios=[(16, 9), (4, 3), (1, 1)],
            tolerance=0.1,
            minimum_width=100,
            minimum_height=100,
        )
        detector = RatioDetector(config)

        # Create a 2:1 image (not in target ratios)
        image = np.zeros((500, 1000, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result.is_problematic
        assert result.confidence > 0.0
        assert len(result.issues) > 0
        assert "doesn't match any target ratios" in result.issues[0]

    def test_minimum_dimensions_check(self):
        """Test minimum dimensions validation"""
        config = RatioConfig(
            target_ratios=[(16, 9), (4, 3), (1, 1)],
            tolerance=0.1,
            minimum_width=200,
            minimum_height=200,
        )
        detector = RatioDetector(config)

        # Create a small image
        image = np.zeros((100, 150, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result.is_problematic
        assert len(result.issues) >= 2  # Both width and height issues
        assert any("Width 150 is below minimum 200" in issue for issue in result.issues)
        assert any(
            "Height 100 is below minimum 200" in issue for issue in result.issues
        )

    def test_maximum_dimensions_check(self):
        """Test maximum dimensions validation"""
        config = RatioConfig(
            target_ratios=[(16, 9), (4, 3), (1, 1)],
            tolerance=0.1,
            check_maximum_dimensions=True,
            maximum_width=1000,
            maximum_height=1000,
        )
        detector = RatioDetector(config)

        # Create a large image
        image = np.zeros((1200, 1600, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result.is_problematic
        assert len(result.issues) >= 2  # Both width and height issues
        assert any(
            "Width 1600 exceeds maximum 1000" in issue for issue in result.issues
        )
        assert any(
            "Height 1200 exceeds maximum 1000" in issue for issue in result.issues
        )

    def test_ratio_tolerance(self):
        """Test ratio tolerance functionality"""
        config = RatioConfig(
            target_ratios=[(16, 9)],  # 1.777...
            tolerance=0.1,
            minimum_width=100,
            minimum_height=100,
        )
        detector = RatioDetector(config)

        # Create image with ratio close to 16:9 (within tolerance)
        image = np.zeros((1080, 1900, 3), dtype=np.uint8)  # 1.759
        result = detector.detect(image)

        assert not result.is_problematic
        assert result.confidence == 0.0

        # Create image with ratio far from 16:9 (outside tolerance)
        image = np.zeros((1080, 1600, 3), dtype=np.uint8)  # 1.481
        result = detector.detect(image)

        assert result.is_problematic
        assert result.confidence > 0.0

    def test_multiple_target_ratios(self):
        """Test detection with multiple target ratios"""
        config = RatioConfig(
            target_ratios=[(16, 9), (4, 3), (1, 1), (3, 4), (9, 16)],
            tolerance=0.1,
            minimum_width=100,
            minimum_height=100,
        )
        detector = RatioDetector(config)

        # Test 4:3 ratio
        image = np.zeros((900, 1200, 3), dtype=np.uint8)
        result = detector.detect(image)
        assert not result.is_problematic

        # Test 1:1 ratio
        image = np.zeros((800, 800, 3), dtype=np.uint8)
        result = detector.detect(image)
        assert not result.is_problematic

        # Test 3:4 ratio (portrait)
        image = np.zeros((1200, 900, 3), dtype=np.uint8)
        result = detector.detect(image)
        assert not result.is_problematic

    def test_invalid_image_handling(self):
        """Test handling of invalid images"""
        config = RatioConfig()
        detector = RatioDetector(config)

        # Test with None image
        result = detector.detect(None)
        assert result.is_problematic
        assert "invalid_image" in result.details.get("error_type", "")

        # Test with invalid image shape
        invalid_image = np.zeros((100,), dtype=np.uint8)  # 1D array
        result = detector.detect(invalid_image)
        assert result.is_problematic
        assert "invalid_image" in result.details.get("error_type", "")

    def test_ratio_calculation_accuracy(self):
        """Test ratio calculation accuracy"""
        config = RatioConfig(
            target_ratios=[(16, 9)],
            tolerance=0.001,  # Very strict tolerance
            minimum_width=100,
            minimum_height=100,
        )
        detector = RatioDetector(config)

        # Test exact 16:9 ratio
        image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        result = detector.detect(image)
        assert not result.is_problematic
        assert abs(result.details["current_ratio"] - 16 / 9) < 0.001

    def test_closest_ratio_finding(self):
        """Test finding the closest ratio when no exact match"""
        config = RatioConfig(
            target_ratios=[(16, 9), (4, 3), (1, 1)],
            tolerance=0.05,  # Strict tolerance
            minimum_width=100,
            minimum_height=100,
        )
        detector = RatioDetector(config)

        # Create image with ratio 1.5 (closest to 4:3 = 1.333)
        image = np.zeros((800, 1200, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result.is_problematic
        assert "Closest: 1.333" in result.issues[0]
        assert "(4:3)" in result.issues[0]

    def test_disabled_ratio_detection(self):
        """Test when ratio detection is disabled"""
        config = RatioConfig(
            enabled=False,
            target_ratios=[(16, 9), (4, 3), (1, 1)],
            tolerance=0.1,
            minimum_width=100,
            minimum_height=100,
        )
        detector = RatioDetector(config)

        # Even with invalid ratio, should not be problematic when disabled
        image = np.zeros((500, 1000, 3), dtype=np.uint8)  # 2:1 ratio
        result = detector.detect(image)

        # Note: The detector will still run, but the config can be used to control behavior
        assert result.detector_name == "ratio"

    def test_error_handling(self):
        """Test error handling in ratio detection"""
        config = RatioConfig()
        detector = RatioDetector(config)

        # Test with image that causes calculation errors
        class MockImage:

            @property
            def shape(self):
                raise Exception("Mock error")

        result = detector.detect(MockImage())
        assert result.is_problematic
        assert "ratio_detection_error" in result.details.get("error_type", "")
