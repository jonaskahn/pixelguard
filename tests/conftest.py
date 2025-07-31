import os
import tempfile
from unittest.mock import Mock

import pytest
from PIL import Image

from src.pixelguard.core.config import (
    DetectionConfig,
    BorderFillConfig,
    UniformColorConfig,
    BackgroundDetectionConfig,
)


@pytest.fixture
def sample_image_path():
    """Create a temporary sample image for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="white")
        img.save(tmp_file.name)
        yield tmp_file.name
        os.unlink(tmp_file.name)


@pytest.fixture
def sample_folder_path():
    """Create a temporary folder with sample images for batch testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create sample images in the folder
        for i in range(3):
            img_path = os.path.join(tmp_dir, f"test_image_{i}.png")
            img = Image.new("RGB", (50, 50), color="white")
            img.save(img_path)
        yield tmp_dir


@pytest.fixture
def mock_detection_config():
    """Create a mock detection configuration."""
    return DetectionConfig(
        border_fill=BorderFillConfig(
            black_fill_threshold=0.05,
            white_fill_threshold=0.05,
        ),
        uniform_color=UniformColorConfig(
            uniform_coverage_threshold=0.85,
            color_delta_threshold=20,
        ),
        background=BackgroundDetectionConfig(
            background_coverage_threshold=0.70,
            background_color_tolerance=20,
        ),
    )


@pytest.fixture
def mock_analysis_result():
    """Create a mock analysis result."""
    result = Mock()
    result.is_problematic = False
    result.width = 100
    result.height = 100
    result.detection_results = []
    result.issues = []
    return result


@pytest.fixture
def mock_problematic_analysis_result():
    """Create a mock problematic analysis result."""
    result = Mock()
    result.is_problematic = True
    result.width = 100
    result.height = 100
    result.detection_results = [
        Mock(
            is_problematic=True,
            detector_name="border_fill",
            issues=["Too much black border"],
            confidence=0.8,
        )
    ]
    result.issues = ["Border fill detected"]
    return result


@pytest.fixture
def mock_file_upload():
    """Create a mock file upload object."""
    mock_file = Mock()
    mock_file.name = "test_image.png"
    mock_file.body = b"fake_image_data"
    return mock_file
