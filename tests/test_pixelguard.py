from unittest.mock import Mock, patch

import pytest

from src.pixelguard import PixelGuard


class TestPixelGuard:
    """Test suite for the main PixelGuard class."""

    def test_pixelguard_init_with_config(self, mock_detection_config):
        """Given a detection config, When PixelGuard is initialized, Then it should use the provided config."""
        # Given
        config = mock_detection_config

        # When
        with patch(
            "src.pixelguard.analyzers.image.ImageAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer

            with patch(
                "src.pixelguard.analyzers.batch.BatchAnalyzer"
            ) as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch

                guard = PixelGuard(config=config)

        # Then
        assert guard.config == config
        mock_analyzer_class.assert_called_once_with(config)
        mock_batch_class.assert_called_once_with(config, image_analyzer=mock_analyzer)

    def test_pixelguard_init_with_mode(self):
        """Given a mode string, When PixelGuard is initialized, Then it should create config from mode."""
        # Given
        mode = "strict"

        # When
        with patch("src.pixelguard.ConfigFactory") as mock_factory:
            mock_config = Mock()
            mock_factory.from_mode.return_value = mock_config

            with patch("src.pixelguard.analyzers.image.ImageAnalyzer"):
                with patch("src.pixelguard.analyzers.batch.BatchAnalyzer"):
                    guard = PixelGuard(mode=mode)

        # Then
        mock_factory.from_mode.assert_called_once()
        assert guard.config == mock_config

    def test_pixelguard_init_without_params(self):
        """Given no parameters, When PixelGuard is initialized, Then it should use default config."""
        # Given
        # No parameters provided

        # When
        with patch("src.pixelguard.ConfigFactory") as mock_factory:
            mock_config = Mock()
            mock_factory.from_mode.return_value = mock_config

            with patch("src.pixelguard.analyzers.image.ImageAnalyzer"):
                with patch("src.pixelguard.analyzers.batch.BatchAnalyzer"):
                    guard = PixelGuard()

        # Then
        mock_factory.from_mode.assert_called_once()
        assert guard.config == mock_config

    def test_analyze_image_success(self, sample_image_path):
        """Given a valid image path, When analyze_image is called, Then it should return analysis result."""
        # Given
        image_path = sample_image_path

        # When
        with patch(
            "src.pixelguard.analyzers.image.ImageAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_result = Mock(is_problematic=False)
            mock_analyzer.analyze.return_value = mock_result
            mock_analyzer_class.return_value = mock_analyzer

            with patch("src.pixelguard.analyzers.batch.BatchAnalyzer"):
                guard = PixelGuard()
                result = guard.analyze_image(image_path)

        # Then
        mock_analyzer.analyze.assert_called_once_with(image_path)
        assert result == mock_result

    def test_analyze_image_exception(self, sample_image_path):
        """Given an image path that causes an exception, When analyze_image is called, Then it should propagate the exception."""
        # Given
        image_path = sample_image_path

        # When
        with patch(
            "src.pixelguard.analyzers.image.ImageAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.side_effect = Exception("Analysis failed")
            mock_analyzer_class.return_value = mock_analyzer

            with patch("src.pixelguard.analyzers.batch.BatchAnalyzer"):
                guard = PixelGuard()

        # Then
        with pytest.raises(Exception, match="Analysis failed"):
            guard.analyze_image(image_path)

    def test_analyze_batch_success(self, sample_folder_path):
        """Given a valid folder path, When analyze_batch is called, Then it should return batch analysis result."""
        # Given
        folder_path = sample_folder_path

        # When
        with patch("src.pixelguard.analyzers.image.ImageAnalyzer"):
            with patch(
                "src.pixelguard.analyzers.batch.BatchAnalyzer"
            ) as mock_batch_class:
                mock_batch = Mock()
                mock_result = Mock()
                mock_batch.process.return_value = mock_result
                mock_batch_class.return_value = mock_batch

                guard = PixelGuard()
                result = guard.analyze_batch(folder_path)

        # Then
        mock_batch.process.assert_called_once_with(folder_path)
        assert result == mock_result

    def test_analyze_batch_exception(self, sample_folder_path):
        """Given a folder path that causes an exception, When analyze_batch is called, Then it should propagate the exception."""
        # Given
        folder_path = sample_folder_path

        # When
        with patch("src.pixelguard.analyzers.image.ImageAnalyzer"):
            with patch(
                "src.pixelguard.analyzers.batch.BatchAnalyzer"
            ) as mock_batch_class:
                mock_batch = Mock()
                mock_batch.process.side_effect = Exception("Batch processing failed")
                mock_batch_class.return_value = mock_batch

                guard = PixelGuard()

        # Then
        with pytest.raises(Exception, match="Batch processing failed"):
            guard.analyze_batch(folder_path)

    def test_pixelguard_with_custom_config_and_mode(self):
        """Given both config and mode, When PixelGuard is initialized, Then it should prioritize config over mode."""
        # Given
        custom_config = Mock()
        mode = "strict"

        # When
        with patch("src.pixelguard.analyzers.image.ImageAnalyzer"):
            with patch("src.pixelguard.analyzers.batch.BatchAnalyzer"):
                guard = PixelGuard(config=custom_config, mode=mode)

        # Then
        assert guard.config == custom_config
        # ConfigFactory should not be called since config is provided
        # This test verifies that config parameter takes precedence

    def test_pixelguard_analyzer_attributes(self):
        """Given PixelGuard instance, When accessed, Then it should have proper analyzer attributes."""
        # Given
        mock_image_analyzer = Mock()
        mock_batch_analyzer = Mock()

        # When
        with patch(
            "src.pixelguard.analyzers.image.ImageAnalyzer",
            return_value=mock_image_analyzer,
        ):
            with patch(
                "src.pixelguard.analyzers.batch.BatchAnalyzer",
                return_value=mock_batch_analyzer,
            ):
                guard = PixelGuard()

        # Then
        assert guard.image_analyzer == mock_image_analyzer
        assert guard.batch_analyzer == mock_batch_analyzer

    def test_pixelguard_config_immutability(self, mock_detection_config):
        """Given a PixelGuard instance, When config is accessed, Then it should return the same config object."""
        # Given
        config = mock_detection_config

        # When
        with patch("src.pixelguard.analyzers.image.ImageAnalyzer"):
            with patch("src.pixelguard.analyzers.batch.BatchAnalyzer"):
                guard = PixelGuard(config=config)

        # Then
        assert guard.config is config
        assert guard.config == config
