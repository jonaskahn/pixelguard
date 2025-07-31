from unittest.mock import Mock, patch

from click.testing import CliRunner

from src.pixelguard.cli.commands import analyze_single_image, analyze_batch, show_config


class TestAnalyzeCommand:
    """Test suite for the AnalyzeCommand CLI function."""

    def test_analyze_command_with_valid_image_path(self, sample_image_path):
        """Given a valid image path, When analyze command is executed, Then it should process the image successfully."""
        # Given
        runner = CliRunner()

        # When
        with patch(
            "src.pixelguard.analyzers.image.ImageAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(is_problematic=False)
            mock_analyzer_class.return_value = mock_analyzer

            with patch(
                "src.pixelguard.reporters.console_reporter.ConsoleReporter"
            ) as mock_reporter_class:
                mock_reporter = Mock()
                mock_reporter_class.return_value = mock_reporter

                result = runner.invoke(analyze_single_image, [sample_image_path])

        # Then
        assert result.exit_code == 0
        mock_analyzer.analyze.assert_called_once_with(sample_image_path)
        mock_reporter.report_single.assert_called_once()

    def test_analyze_command_with_custom_thresholds(self, sample_image_path):
        """Given custom threshold parameters, When analyze command is executed, Then it should use the custom thresholds."""
        # Given
        runner = CliRunner()
        custom_thresholds = [
            "--border-fill-threshold",
            "0.1",
            "--uniform-threshold",
            "0.9",
            "--background-threshold",
            "0.8",
            "--color-tolerance",
            "30",
        ]

        # When
        with patch(
            "src.pixelguard.analyzers.image.ImageAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(is_problematic=False)
            mock_analyzer_class.return_value = mock_analyzer

            with patch("src.pixelguard.reporters.console_reporter.ConsoleReporter"):
                result = runner.invoke(
                    analyze_single_image, [sample_image_path] + custom_thresholds
                )

        # Then
        assert result.exit_code == 0
        mock_analyzer_class.assert_called_once()
        # Verify the config was created with custom thresholds
        call_args = mock_analyzer_class.call_args
        config = call_args[0][0]  # First argument is the config
        assert config.border_fill.black_fill_threshold == 0.1
        assert config.uniform_color.uniform_coverage_threshold == 0.9
        assert config.background.background_coverage_threshold == 0.8
        assert config.uniform_color.color_delta_threshold == 30

    def test_analyze_command_with_invalid_image_path(self):
        """Given an invalid image path, When analyze command is executed, Then it should fail gracefully."""
        # Given
        runner = CliRunner()
        invalid_path = "/nonexistent/image.png"

        # When
        result = runner.invoke(analyze_single_image, [invalid_path])

        # Then
        assert result.exit_code != 0
        assert "does not exist" in result.output


class TestBatchCommand:
    """Test suite for the BatchCommand CLI function."""

    def test_batch_command_with_valid_folder(self, sample_folder_path):
        """Given a valid folder path, When batch command is executed, Then it should process all images."""
        # Given
        runner = CliRunner()

        # When
        with patch("src.pixelguard.cli.commands.PixelGuard") as mock_pixelguard_class:
            mock_guard = Mock()
            mock_report = Mock()
            mock_guard.analyze_batch.return_value = mock_report
            mock_pixelguard_class.return_value = mock_guard

            with patch(
                "src.pixelguard.reporters.console_reporter.ConsoleReporter"
            ) as mock_reporter_class:
                mock_reporter = Mock()
                mock_reporter_class.return_value = mock_reporter

                result = runner.invoke(analyze_batch, [sample_folder_path])

        # Then
        assert result.exit_code == 0
        mock_guard.analyze_batch.assert_called_once_with(sample_folder_path)
        mock_reporter.report_batch.assert_called_once_with(mock_report)

    def test_batch_command_with_json_output(self, sample_folder_path):
        """Given JSON format and output file, When batch command is executed, Then it should use JSON reporter."""
        # Given
        runner = CliRunner()

        # When
        with patch("src.pixelguard.cli.commands.PixelGuard") as mock_pixelguard_class:
            mock_guard = Mock()
            mock_report = Mock()
            mock_guard.analyze_batch.return_value = mock_report
            mock_pixelguard_class.return_value = mock_guard

            with patch(
                "src.pixelguard.reporters.json_reporter.JSONReporter"
            ) as mock_json_reporter_class:
                mock_json_reporter = Mock()
                mock_json_reporter_class.return_value = mock_json_reporter

                result = runner.invoke(
                    analyze_batch,
                    [
                        sample_folder_path,
                        "--format",
                        "json",
                        "--output",
                        "test_output.json",
                    ],
                )

        # Then
        assert result.exit_code == 0
        mock_json_reporter_class.assert_called_once_with("test_output.json")
        mock_json_reporter.report_batch.assert_called_once_with(mock_report)

    def test_batch_command_with_csv_output(self, sample_folder_path):
        """Given CSV format and output file, When batch command is executed, Then it should use CSV reporter."""
        # Given
        runner = CliRunner()

        # When
        with patch("src.pixelguard.cli.commands.PixelGuard") as mock_pixelguard_class:
            mock_guard = Mock()
            mock_report = Mock()
            mock_guard.analyze_batch.return_value = mock_report
            mock_pixelguard_class.return_value = mock_guard

            with patch(
                "src.pixelguard.reporters.csv_reporter.CSVReporter"
            ) as mock_csv_reporter_class:
                mock_csv_reporter = Mock()
                mock_csv_reporter_class.return_value = mock_csv_reporter

                result = runner.invoke(
                    analyze_batch,
                    [
                        sample_folder_path,
                        "--format",
                        "csv",
                        "--output",
                        "test_output.csv",
                    ],
                )

        # Then
        assert result.exit_code == 0
        mock_csv_reporter_class.assert_called_once_with("test_output.csv")
        mock_csv_reporter.report_batch.assert_called_once_with(mock_report)

    def test_batch_command_with_custom_mode(self, sample_folder_path):
        """Given a custom mode, When batch command is executed, Then it should use the specified mode."""
        # Given
        runner = CliRunner()

        # When
        with patch("src.pixelguard.cli.commands.PixelGuard") as mock_pixelguard_class:
            mock_guard = Mock()
            mock_guard.analyze_batch.return_value = Mock()
            mock_pixelguard_class.return_value = mock_guard

            with patch("src.pixelguard.reporters.console_reporter.ConsoleReporter"):
                result = runner.invoke(
                    analyze_batch, [sample_folder_path, "--mode", "strict"]
                )

        # Then
        assert result.exit_code == 0
        mock_pixelguard_class.assert_called_once_with(mode="strict")


class TestConfigCommand:
    """Test suite for the ConfigCommand CLI function."""

    def test_config_command_without_mode(self):
        """Given no mode parameter, When config command is executed, Then it should show available modes."""
        # Given
        runner = CliRunner()

        # When
        result = runner.invoke(show_config, [])

        # Then
        assert result.exit_code == 0
        assert "Available modes:" in result.output
        assert "strict" in result.output
        assert "default" in result.output
        assert "lenient" in result.output

    def test_config_command_with_valid_mode(self):
        """Given a valid mode, When config command is executed, Then it should display the configuration."""
        # Given
        runner = CliRunner()

        # When
        with patch("src.pixelguard.core.config.ConfigFactory") as mock_factory:
            mock_config = Mock()
            mock_config.__str__ = lambda self: "Mock Config"
            mock_factory.from_mode.return_value = mock_config

            # Mock the DetectionMode enum to avoid the actual enum lookup
            with patch("src.pixelguard.core.config.DetectionMode") as mock_enum:
                mock_enum.return_value = "STRICT"
                result = runner.invoke(show_config, ["strict"])

        # Then
        assert result.exit_code == 0
        mock_factory.from_mode.assert_called_once()
        assert "Mock Config" in result.output

    def test_config_command_with_invalid_mode(self):
        """Given an invalid mode, When config command is executed, Then it should show an error message."""
        # Given
        runner = CliRunner()

        # When
        with patch("src.pixelguard.core.config.ConfigFactory") as mock_factory:
            mock_factory.from_mode.side_effect = Exception("Invalid mode")

            result = runner.invoke(show_config, ["invalid_mode"])

        # Then
        assert result.exit_code == 0
        assert "Invalid mode: invalid_mode" in result.output
