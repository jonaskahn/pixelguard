import os
from unittest.mock import patch

from src.pixelguard.core.config import ConfigFactory, DetectionMode


class TestCustomConfig:
    """Test suite for custom configuration from environment variables"""

    def test_custom_config_creation(self):
        """Test that custom config can be created"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)
        assert config is not None
        assert hasattr(config, "border_fill")
        assert hasattr(config, "uniform_color")
        assert hasattr(config, "background")
        assert hasattr(config, "ratio")

    @patch.dict(
        os.environ,
        {
            "PXG_BORDER_FILL_BLACK_FILL_THRESHOLD": "0.03",
            "PXG_RATIO_TOLERANCE": "0.05",
            "PXG_RATIO_TARGET_RATIOS": "16:9,4:3,1:1",
            "PXG_DETECTOR_BORDER_FILL_ENABLED": "true",
            "PXG_DETECTOR_RATIO_ENABLED": "true",
        },
    )
    def test_custom_config_with_env_vars(self):
        """Test custom config with environment variables"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

        # Check border fill config
        assert config.border_fill.black_fill_threshold == 0.03

        # Check ratio config
        assert config.ratio.tolerance == 0.05
        assert config.ratio.target_ratios == [(16, 9), (4, 3), (1, 1)]

        # Check enabled detectors
        assert "border_fill" in config.enabled_detectors
        assert "ratio" in config.enabled_detectors

    @patch.dict(
        os.environ,
        {
            "PXG_UNIFORM_COLOR_SPACE": "RGB",
            "PXG_UNIFORM_COLOR_COVERAGE_THRESHOLD": "0.90",
            "PXG_BACKGROUND_DETECTION_METHOD": "histogram",
            "PXG_BACKGROUND_COVERAGE_THRESHOLD": "0.75",
        },
    )
    def test_custom_config_different_detectors(self):
        """Test custom config with different detector settings"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

        # Check uniform color config
        assert config.uniform_color.color_space == "RGB"
        assert config.uniform_color.uniform_coverage_threshold == 0.90

        # Check background config
        assert config.background.detection_method == "histogram"
        assert config.background.background_coverage_threshold == 0.75

    @patch.dict(
        os.environ,
        {
            "PXG_RATIO_ENABLED": "false",
            "PXG_RATIO_CHECK_MINIMUM_DIMENSIONS": "true",
            "PXG_RATIO_CHECK_MAXIMUM_DIMENSIONS": "true",
            "PXG_RATIO_MINIMUM_WIDTH": "500",
            "PXG_RATIO_MAXIMUM_WIDTH": "2000",
        },
    )
    def test_custom_config_boolean_values(self):
        """Test custom config with boolean environment variables"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

        # Check ratio config
        assert config.ratio.enabled == False
        assert config.ratio.check_minimum_dimensions == True
        assert config.ratio.check_maximum_dimensions == True
        assert config.ratio.minimum_width == 500
        assert config.ratio.maximum_width == 2000

    def test_custom_config_defaults(self):
        """Test custom config uses defaults when env vars not set"""
        # Clear any existing env vars
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

            # Check defaults
            assert config.border_fill.black_fill_threshold == 0.05
            assert config.uniform_color.color_space == "LAB"
            assert config.background.detection_method == "edge_based"
            assert config.ratio.tolerance == 0.1

    @patch.dict(os.environ, {"PXG_RATIO_TARGET_RATIOS": "invalid_format"})
    def test_custom_config_invalid_values(self):
        """Test custom config handles invalid environment variable values"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

        # Should fall back to defaults for invalid values
        assert config.ratio.target_ratios == [(16, 9), (4, 3), (1, 1), (3, 4), (9, 16)]
        assert "border_fill" in config.enabled_detectors
        assert "uniform_color" in config.enabled_detectors
        assert "background" in config.enabled_detectors
        assert "ratio" in config.enabled_detectors

    @patch.dict(
        os.environ,
        {
            "PXG_RATIO_TARGET_RATIOS": "16:9,4:3,1:1,21:9",
            "PXG_BORDER_FILL_BLACK_THRESHOLD": "25",
            "PXG_UNIFORM_COLOR_DELTA_THRESHOLD": "20",
            "PXG_BACKGROUND_COLOR_TOLERANCE": "30",
        },
    )
    def test_custom_config_mixed_types(self):
        """Test custom config with mixed data types"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

        # Check ratio config
        assert config.ratio.target_ratios == [(16, 9), (4, 3), (1, 1), (21, 9)]

        # Check integer values
        assert config.border_fill.black_threshold == 25
        assert config.uniform_color.color_delta_threshold == 20
        assert config.background.background_color_tolerance == 30

    def test_env_var_parsing_methods(self):
        """Test the environment variable parsing helper methods"""
        # Test float parsing
        assert ConfigFactory._get_environment_float("NONEXISTENT", 0.5) == 0.5
        with patch.dict(os.environ, {"TEST_FLOAT": "0.75"}):
            assert ConfigFactory._get_environment_float("TEST_FLOAT", 0.5) == 0.75

        # Test int parsing
        assert ConfigFactory._get_environment_int("NONEXISTENT", 100) == 100
        with patch.dict(os.environ, {"TEST_INT": "200"}):
            assert ConfigFactory._get_environment_int("TEST_INT", 100) == 200

        # Test bool parsing
        assert ConfigFactory._get_environment_bool("NONEXISTENT", True) == True
        with patch.dict(os.environ, {"TEST_BOOL": "true"}):
            assert ConfigFactory._get_environment_bool("TEST_BOOL", False) == True
        with patch.dict(os.environ, {"TEST_BOOL": "false"}):
            assert ConfigFactory._get_environment_bool("TEST_BOOL", True) == False

        # Test string parsing
        assert ConfigFactory._get_environment_string("NONEXISTENT", "default") == "default"
        with patch.dict(os.environ, {"TEST_STR": "custom"}):
            assert ConfigFactory._get_environment_string("TEST_STR", "default") == "custom"

    def test_ratio_parsing(self):
        """Test ratio list parsing from environment variable"""
        # Test valid ratio format
        with patch.dict(os.environ, {"TEST_RATIOS": "16:9,4:3,1:1"}):
            ratios = ConfigFactory._get_env_ratios("TEST_RATIOS", [(1, 1)])
            assert ratios == [(16, 9), (4, 3), (1, 1)]

        # Test invalid format - should return default
        with patch.dict(os.environ, {"TEST_RATIOS": "invalid"}):
            ratios = ConfigFactory._get_env_ratios("TEST_RATIOS", [(1, 1)])
            assert ratios == [(1, 1)]

        # Test empty value - should return default
        with patch.dict(os.environ, {"TEST_RATIOS": ""}):
            ratios = ConfigFactory._get_env_ratios("TEST_RATIOS", [(1, 1)])
            assert ratios == [(1, 1)]

    @patch.dict(
        os.environ,
        {
            "PXG_DETECTOR_BORDER_FILL_ENABLED": "true",
            "PXG_DETECTOR_UNIFORM_COLOR_ENABLED": "false",
            "PXG_DETECTOR_BACKGROUND_ENABLED": "true",
            "PXG_DETECTOR_RATIO_ENABLED": "false",
        },
    )
    def test_custom_config_individual_detector_enable(self):
        """Test custom config with individual detector enable flags"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

        # Check enabled detectors
        assert "border_fill" in config.enabled_detectors
        assert "uniform_color" not in config.enabled_detectors
        assert "background" in config.enabled_detectors
        assert "ratio" not in config.enabled_detectors

    @patch.dict(
        os.environ,
        {
            "PXG_DETECTOR_BORDER_FILL_ENABLED": "false",
            "PXG_DETECTOR_UNIFORM_COLOR_ENABLED": "false",
            "PXG_DETECTOR_BACKGROUND_ENABLED": "false",
            "PXG_DETECTOR_RATIO_ENABLED": "false",
        },
    )
    def test_custom_config_all_detectors_disabled(self):
        """Test custom config when all individual detectors are disabled"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

        # All detectors should be disabled
        assert len(config.enabled_detectors) == 0

    @patch.dict(
        os.environ,
        {
            "PXG_DETECTOR_BORDER_FILL_ENABLED": "true",
            "PXG_DETECTOR_UNIFORM_COLOR_ENABLED": "true",
            "PXG_DETECTOR_BACKGROUND_ENABLED": "true",
            "PXG_DETECTOR_RATIO_ENABLED": "true",
        },
    )
    def test_custom_config_all_detectors_enabled(self):
        """Test custom config when all individual detectors are enabled"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

        # All detectors should be enabled
        assert "border_fill" in config.enabled_detectors
        assert "uniform_color" in config.enabled_detectors
        assert "background" in config.enabled_detectors
        assert "ratio" in config.enabled_detectors

    @patch.dict(
        os.environ,
        {
            "PXG_DETECTOR_BORDER_FILL_ENABLED": "invalid",
            "PXG_DETECTOR_UNIFORM_COLOR_ENABLED": "yes",
            "PXG_DETECTOR_BACKGROUND_ENABLED": "1",
            "PXG_DETECTOR_RATIO_ENABLED": "on",
        },
    )
    def test_custom_config_boolean_parsing(self):
        """Test custom config with various boolean formats"""
        config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

        # Invalid should default to False, others should parse correctly
        assert (
            "border_fill" not in config.enabled_detectors
        )  # Invalid defaults to False
        assert "uniform_color" in config.enabled_detectors  # 'yes' = True
        assert "background" in config.enabled_detectors  # '1' = True
        assert "ratio" in config.enabled_detectors  # 'on' = True

    def test_custom_config_detector_enable_defaults(self):
        """Test custom config uses defaults when detector enable flags not set"""
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigFactory.from_mode(DetectionMode.CUSTOM)

            # All detectors should be enabled by default
            assert "border_fill" in config.enabled_detectors
            assert "uniform_color" in config.enabled_detectors
            assert "background" in config.enabled_detectors
            assert "ratio" in config.enabled_detectors
