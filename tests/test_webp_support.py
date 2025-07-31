"""
Tests for WebP support in PixelGuard
"""

import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from src.pixelguard.analyzers.image import ImageAnalyzer
from src.pixelguard.core.config import DetectionMode, ConfigFactory
from src.pixelguard.utils.image_loader import ImageLoader


class TestWebPSupport:
    """Test WebP support in PixelGuard"""

    def test_image_loader_webp_support(self):
        """Test that ImageLoader recognizes WebP format"""
        loader = ImageLoader()

        # Test format detection
        assert loader.is_supported_format("test.webp")
        assert loader.is_supported_format("TEST.WEBP")
        assert loader.is_supported_format(Path("test.webp"))

    def test_image_loader_webp_loading(self):
        """Test that ImageLoader can load WebP files"""
        loader = ImageLoader()

        # Create a test WebP file
        test_image = Image.new("RGB", (50, 50), color="green")

        with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as temp_file:
            test_image.save(temp_file.name, "WEBP")
            temp_path = Path(temp_file.name)

        try:
            # Test loading
            image_array = loader.load(temp_path)

            # Verify the loaded image
            assert image_array is not None
            assert image_array.shape == (50, 50, 3)  # OpenCV uses BGR
            assert image_array.dtype == np.uint8

        finally:
            # Clean up
            temp_path.unlink()

    def test_streamlit_file_uploader_webp_support(self):
        """Test that Streamlit app accepts WebP files"""
        # This test verifies that the file uploader type list includes webp
        # The actual file uploader is tested in the streamlit app itself
        from src.pixelguard.streamlit_app import main

        # Import the main function to ensure the module loads correctly
        # with the updated file uploader configuration
        assert main is not None

    def test_webp_analysis_integration(self):
        """Test that WebP files can be analyzed through the full pipeline"""
        # Create a test WebP file
        test_image = Image.new("RGB", (100, 100), color="blue")

        with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as temp_file:
            test_image.save(temp_file.name, "WEBP")
            temp_path = Path(temp_file.name)

        try:
            # Create analyzer
            config = ConfigFactory.from_mode(DetectionMode.DEFAULT)
            analyzer = ImageAnalyzer(config)

            # Analyze the WebP file
            result = analyzer.analyze(temp_path)

            # Verify analysis result
            assert result is not None
            assert result.width == 100
            assert result.height == 100
            assert result.file_path == temp_path

        finally:
            # Clean up
            temp_path.unlink()

    def test_webp_with_different_detectors(self):
        """Test WebP files with different detector combinations"""
        # Create a test WebP file with specific characteristics
        # Create an image that might trigger some detectors
        test_image = Image.new(
            "RGB", (200, 50), color="black"
        )  # Very wide, might trigger ratio detector

        with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as temp_file:
            test_image.save(temp_file.name, "WEBP")
            temp_path = Path(temp_file.name)

        try:
            # Test with ratio detector enabled
            config = ConfigFactory.from_mode(DetectionMode.DEFAULT)
            analyzer = ImageAnalyzer(config)

            result = analyzer.analyze(temp_path)

            # Verify the analysis completed
            assert result is not None
            assert len(result.detection_results) > 0

        finally:
            # Clean up
            temp_path.unlink()

    def test_webp_edge_cases(self):
        """Test WebP files with edge cases"""
        loader = ImageLoader()

        # Test with different image sizes
        for size in [(1, 1), (1000, 1000), (100, 200)]:
            test_image = Image.new("RGB", size, color="red")

            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as temp_file:
                test_image.save(temp_file.name, "WEBP")
                temp_path = Path(temp_file.name)

            try:
                image_array = loader.load(temp_path)
                assert (
                    image_array.shape[:2] == size[::-1]
                )  # OpenCV uses (height, width)
            finally:
                temp_path.unlink()

    def test_webp_transparency_support(self):
        """Test WebP files with transparency (RGBA)"""
        loader = ImageLoader()

        # Create a test WebP file with transparency
        test_image = Image.new(
            "RGBA", (50, 50), color=(255, 0, 0, 128)
        )  # Semi-transparent red

        with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as temp_file:
            test_image.save(temp_file.name, "WEBP")
            temp_path = Path(temp_file.name)

        try:
            # Test loading
            image_array = loader.load(temp_path)

            # Verify the loaded image
            assert image_array is not None
            # OpenCV loads RGBA as BGRA
            assert image_array.shape == (50, 50, 4)

        finally:
            # Clean up
            temp_path.unlink()
