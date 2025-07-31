import numpy as np

from src.pixelguard.core.config import BackgroundDetectionConfig
from src.pixelguard.detectors.background import BackgroundDetector


class TestBackgroundDetector:
    """Test cases for background detection"""

    def test_dark_blue_background_detection(self):
        """Test that dark blue background is properly detected"""
        # Create a test image with dark blue background and white content area
        height, width = 400, 600

        # Create dark blue background (BGR format)
        dark_blue = np.array([139, 69, 19], dtype=np.uint8)  # Dark blue in BGR
        image = np.full((height, width, 3), dark_blue, dtype=np.uint8)

        # Add white content area in the center (like the Sharpie marker card)
        content_start_h = height // 4
        content_end_h = 3 * height // 4
        content_start_w = width // 6
        content_end_w = 5 * width // 6

        white = np.array([255, 255, 255], dtype=np.uint8)
        image[content_start_h:content_end_h, content_start_w:content_end_w] = white

        # Create detector with appropriate config
        config = BackgroundDetectionConfig(
            detection_method="edge_based",
            background_coverage_threshold=0.60,
            background_color_tolerance=30,
        )
        detector = BackgroundDetector(config)

        # Detect background
        result = detector.detect(image)

        # Verify results
        assert result.is_problematic == True
        assert result.confidence > 0.6
        assert "Background dominates" in result.issues[0]

        # Check that detected background color is close to dark blue
        detected_color = np.array(result.details["background_color"])
        color_distance = np.linalg.norm(detected_color - dark_blue)
        assert color_distance < 50  # Should be reasonably close

    def test_edge_based_detection(self):
        """Test edge-based background detection"""
        height, width = 300, 400

        # Create image with red background and green center
        red_bg = np.array([0, 0, 255], dtype=np.uint8)  # Red in BGR
        image = np.full((height, width, 3), red_bg, dtype=np.uint8)

        # Add green center
        green_center = np.array([0, 255, 0], dtype=np.uint8)  # Green in BGR
        center_h, center_w = height // 4, width // 4
        image[center_h : 3 * center_h, center_w : 3 * center_w] = green_center

        config = BackgroundDetectionConfig(
            detection_method="edge_based", background_coverage_threshold=0.70
        )
        detector = BackgroundDetector(config)

        result = detector.detect(image)

        # Should detect red as background
        detected_color = np.array(result.details["background_color"])
        color_distance = np.linalg.norm(detected_color - red_bg)
        assert color_distance < 50

    def test_corner_based_detection(self):
        """Test corner-based background detection"""
        height, width = 300, 400

        # Create image with blue background and white corners
        blue_bg = np.array([255, 0, 0], dtype=np.uint8)  # Blue in BGR
        image = np.full((height, width, 3), blue_bg, dtype=np.uint8)

        # Add white center
        white_center = np.array([255, 255, 255], dtype=np.uint8)
        center_h, center_w = height // 4, width // 4
        image[center_h : 3 * center_h, center_w : 3 * center_w] = white_center

        config = BackgroundDetectionConfig(
            detection_method="corner_based", background_coverage_threshold=0.70
        )
        detector = BackgroundDetector(config)

        result = detector.detect(image)

        # Should detect blue as background
        detected_color = np.array(result.details["background_color"])
        color_distance = np.linalg.norm(detected_color - blue_bg)
        assert color_distance < 50

    def test_histogram_based_detection(self):
        """Test histogram-based background detection"""
        height, width = 300, 400

        # Create image with green background and small red object
        green_bg = np.array([0, 255, 0], dtype=np.uint8)  # Green in BGR
        image = np.full((height, width, 3), green_bg, dtype=np.uint8)

        # Add small red object
        red_object = np.array([0, 0, 255], dtype=np.uint8)  # Red in BGR
        object_h, object_w = height // 8, width // 8
        image[object_h : 2 * object_h, object_w : 2 * object_w] = red_object

        config = BackgroundDetectionConfig(
            detection_method="histogram_based", background_coverage_threshold=0.80
        )
        detector = BackgroundDetector(config)

        result = detector.detect(image)

        # Should detect green as background
        detected_color = np.array(result.details["background_color"])
        color_distance = np.linalg.norm(detected_color - green_bg)
        assert color_distance < 50

    def test_no_background_dominance(self):
        """Test case where background doesn't dominate"""
        height, width = 300, 400

        # Create image with equal parts of two colors
        color1 = np.array([255, 0, 0], dtype=np.uint8)  # Blue
        color2 = np.array([0, 255, 0], dtype=np.uint8)  # Green

        image = np.full((height, width, 3), color1, dtype=np.uint8)
        image[:, width // 2 :] = color2

        config = BackgroundDetectionConfig(
            detection_method="edge_based", background_coverage_threshold=0.60
        )
        detector = BackgroundDetector(config)

        result = detector.detect(image)

        # Should not be problematic since no single color dominates
        assert result.is_problematic == False
        assert result.confidence < 0.6
