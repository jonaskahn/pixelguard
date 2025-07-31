from pathlib import Path
from unittest.mock import Mock, patch

from src.pixelguard.core.config import DetectionMode
from src.pixelguard.streamlit_app import (
    create_image_analyzer,
    analyze_single_image,
    display_detection_result,
    process_uploaded_file,
    main,
)


class TestCreateImageAnalyzer:
    """Test suite for the create_image_analyzer function."""

    def test_create_image_analyzer_with_default_mode(self):
        """Given default mode, When create_image_analyzer is called, Then it should create analyzer with default config."""
        # Given
        # When
        with patch("src.pixelguard.streamlit_app.ConfigFactory") as mock_factory:
            mock_config = Mock()
            mock_factory.from_mode.return_value = mock_config

            with patch(
                "src.pixelguard.streamlit_app.ImageAnalyzer"
            ) as mock_analyzer_class:
                mock_analyzer = Mock()
                mock_analyzer_class.return_value = mock_analyzer

                analyzer = create_image_analyzer()

        # Then
        mock_factory.from_mode.assert_called_once_with(DetectionMode.DEFAULT)
        mock_analyzer_class.assert_called_once_with(mock_config)
        assert analyzer == mock_analyzer

    def test_create_image_analyzer_with_custom_detectors(self):
        """Given custom detectors, When create_image_analyzer is called, Then it should create analyzer with custom config."""
        # Given
        custom_detectors = ["border_fill", "ratio"]

        # When
        with patch("src.pixelguard.streamlit_app.ConfigFactory") as mock_factory:
            mock_config = Mock()
            mock_factory.from_mode.return_value = mock_config

            with patch(
                "src.pixelguard.streamlit_app.ImageAnalyzer"
            ) as mock_analyzer_class:
                mock_analyzer = Mock()
                mock_analyzer_class.return_value = mock_analyzer

                analyzer = create_image_analyzer(custom_detectors)

        # Then
        mock_factory.from_mode.assert_called_once_with(DetectionMode.DEFAULT)
        mock_analyzer_class.assert_called_once()
        assert analyzer == mock_analyzer


class TestAnalyzeSingleImage:
    """Test suite for the analyze_single_image function."""

    def test_analyze_single_image_success(self, sample_image_path):
        """Given a valid image path, When analyze_single_image is called, Then it should return analysis result."""
        # Given
        image_path = Path(sample_image_path)
        mock_analyzer = Mock()
        mock_result = Mock(is_problematic=False)
        mock_analyzer.analyze.return_value = mock_result

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            result = analyze_single_image(image_path, mock_analyzer)

        # Then
        mock_analyzer.analyze.assert_called_once_with(image_path)
        assert result == mock_result
        mock_st.error.assert_not_called()

    def test_analyze_single_image_exception(self, sample_image_path):
        """Given an image path that causes an exception, When analyze_single_image is called, Then it should show error and return None."""
        # Given
        image_path = Path(sample_image_path)
        mock_analyzer = Mock()
        mock_analyzer.analyze.side_effect = Exception("Analysis failed")

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            result = analyze_single_image(image_path, mock_analyzer)

        # Then
        mock_analyzer.analyze.assert_called_once_with(image_path)
        assert result is None
        mock_st.error.assert_called_once_with(
            f"Error analyzing {image_path.name}: Analysis failed"
        )


class TestDisplayDetectionResult:
    """Test suite for the display_detection_result function."""

    def test_display_detection_result_passed(self):
        """Given a passed detection result, When display_detection_result is called, Then it should show green status."""
        # Given
        result = Mock()
        result.is_problematic = False
        result.confidence = 0.85
        result.details = {"coverage": "0.75"}
        result.issues = []
        detector_name = "border_fill"

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            # Mock the write method to capture the call
            mock_st.write = Mock()
            display_detection_result(result, detector_name)

        # Then
        mock_st.write.assert_called()
        # Check that the status shows green (passed) - look for the first call which should be the status
        first_call = mock_st.write.call_args_list[0][0][0]
        assert "🟢" in first_call
        assert "Passed" in first_call
        assert "0.85" in first_call

    def test_display_detection_result_problematic(self):
        """Given a problematic detection result, When display_detection_result is called, Then it should show red status."""
        # Given
        result = Mock()
        result.is_problematic = True
        result.confidence = 0.95
        result.details = {"coverage": "0.90"}
        result.issues = ["Too much border detected"]
        detector_name = "border_fill"

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            # Mock the write method to capture the call
            mock_st.write = Mock()
            display_detection_result(result, detector_name)

        # Then
        mock_st.write.assert_called()
        # Check that the status shows red (problematic) - look for the first call which should be the status
        first_call = mock_st.write.call_args_list[0][0][0]
        assert "🔴" in first_call
        assert "Problematic" in first_call
        assert "0.95" in first_call

    def test_display_detection_result_with_details(self):
        """Given a result with details, When display_detection_result is called, Then it should show expandable details."""
        # Given
        result = Mock()
        result.is_problematic = False
        result.confidence = 0.80
        result.details = {"coverage": "0.75", "threshold": "0.70"}
        result.issues = []
        detector_name = "uniform_color"

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            display_detection_result(result, detector_name)

        # Then
        # Should call st.expander for details
        mock_st.expander.assert_called_with("Details for uniform_color")

    def test_display_detection_result_with_issues(self):
        """Given a result with issues, When display_detection_result is called, Then it should show expandable issues."""
        # Given
        result = Mock()
        result.is_problematic = True
        result.confidence = 0.90
        result.details = {}
        result.issues = ["Issue 1", "Issue 2"]
        detector_name = "background"

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            display_detection_result(result, detector_name)

        # Then
        # Should call st.expander for issues
        mock_st.expander.assert_called_with("Issues for background")


class TestDisplayResult:
    """Test suite for the display_result function."""

    def test_display_result_success(self, sample_image_path):
        """Given a successful analysis result, When display_result is called, Then it should display the result properly."""
        # Given
        image_path = Path(sample_image_path)
        analysis = Mock()
        analysis.is_problematic = False
        analysis.width = 100
        analysis.height = 100
        analysis.detection_results = []

        uploaded_file = Mock()
        uploaded_file.name = "test_image.png"

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            # Mock st.container to return a context manager
            mock_container = Mock()
            mock_container.__enter__ = Mock(return_value=None)
            mock_container.__exit__ = Mock(return_value=None)
            mock_st.container.return_value = mock_container

            # Mock st.columns to return two mock columns that support context managers
            mock_col1 = Mock()
            mock_col1.__enter__ = Mock(return_value=None)
            mock_col1.__exit__ = Mock(return_value=None)
            mock_col2 = Mock()
            mock_col2.__enter__ = Mock(return_value=None)
            mock_col2.__exit__ = Mock(return_value=None)
            mock_st.columns.return_value = [mock_col1, mock_col2]

            with patch("src.pixelguard.streamlit_app.Image") as mock_pil:
                mock_image = Mock()
                mock_pil.open.return_value = mock_image

                display_result(image_path, analysis, uploaded_file)

        # Then
        mock_st.markdown.assert_called()
        mock_st.write.assert_called()
        # Check that it shows passed status
        markdown_calls = [
            call for call in mock_st.markdown.call_args_list if "PASSED" in str(call)
        ]
        assert len(markdown_calls) > 0

    def test_display_result_problematic(self, sample_image_path):
        """Given a problematic analysis result, When display_result is called, Then it should display problematic status."""
        # Given
        image_path = Path(sample_image_path)
        analysis = Mock()
        analysis.is_problematic = True
        analysis.width = 100
        analysis.height = 100
        analysis.detection_results = []

        uploaded_file = Mock()
        uploaded_file.name = "test_image.png"

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            # Mock st.container to return a context manager
            mock_container = Mock()
            mock_container.__enter__ = Mock(return_value=None)
            mock_container.__exit__ = Mock(return_value=None)
            mock_st.container.return_value = mock_container

            # Mock st.columns to return two mock columns that support context managers
            mock_col1 = Mock()
            mock_col1.__enter__ = Mock(return_value=None)
            mock_col1.__exit__ = Mock(return_value=None)
            mock_col2 = Mock()
            mock_col2.__enter__ = Mock(return_value=None)
            mock_col2.__exit__ = Mock(return_value=None)
            mock_st.columns.return_value = [mock_col1, mock_col2]

            with patch("src.pixelguard.streamlit_app.Image") as mock_pil:
                mock_image = Mock()
                mock_pil.open.return_value = mock_image

                display_result(image_path, analysis, uploaded_file)

        # Then
        # Check that it shows problematic status
        markdown_calls = [
            call
            for call in mock_st.markdown.call_args_list
            if "PROBLEMATIC" in str(call)
        ]
        assert len(markdown_calls) > 0

    def test_display_result_image_error(self, sample_image_path):
        """Given an image loading error, When display_result is called, Then it should show error message."""
        # Given
        image_path = Path(sample_image_path)
        analysis = Mock()
        analysis.is_problematic = False
        analysis.width = 100
        analysis.height = 100
        analysis.detection_results = []

        uploaded_file = Mock()
        uploaded_file.name = "test_image.png"

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            # Mock st.container to return a context manager
            mock_container = Mock()
            mock_container.__enter__ = Mock(return_value=None)
            mock_container.__exit__ = Mock(return_value=None)
            mock_st.container.return_value = mock_container

            # Mock st.columns to return two mock columns that support context managers
            mock_col1 = Mock()
            mock_col1.__enter__ = Mock(return_value=None)
            mock_col1.__exit__ = Mock(return_value=None)
            mock_col2 = Mock()
            mock_col2.__enter__ = Mock(return_value=None)
            mock_col2.__exit__ = Mock(return_value=None)
            mock_st.columns.return_value = [mock_col1, mock_col2]

            with patch("src.pixelguard.streamlit_app.Image") as mock_pil:
                mock_pil.open.side_effect = Exception("Image load failed")

                display_result(image_path, analysis, uploaded_file)

        # Then
        mock_st.error.assert_called_with("Error loading image: Image load failed")

    def test_display_result_none_analysis(self, sample_image_path):
        """Given None analysis, When display_result is called, Then it should return early."""
        # Given
        image_path = Path(sample_image_path)
        analysis = None
        uploaded_file = Mock()
        uploaded_file.name = "test_image.png"

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            display_result(image_path, analysis, uploaded_file)

        # Then
        # Should not call any st methods since analysis is None
        mock_st.markdown.assert_not_called()
        mock_st.write.assert_not_called()


class TestProcessUploadedFile:
    """Test suite for the process_uploaded_file function."""

    def test_process_uploaded_file_success(self):
        """Given a valid uploaded file, When process_uploaded_file is called, Then it should process the file successfully."""
        # Given
        uploaded_file = Mock()
        uploaded_file.name = "test_image.png"
        uploaded_file.getvalue.return_value = b"fake_image_data"

        mock_analyzer = Mock()
        mock_analysis = Mock(is_problematic=False)
        mock_analyzer.analyze.return_value = mock_analysis

        # When
        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            mock_temp = Mock()
            mock_temp.name = "/tmp/test_image.png"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            with patch("src.pixelguard.streamlit_app.analyze_image") as mock_analyze:
                mock_analyze.return_value = mock_analysis

                with patch(
                    "src.pixelguard.streamlit_app.display_result"
                ) as mock_display:
                    with patch("os.unlink") as mock_unlink:
                        process_uploaded_file(uploaded_file, mock_analyzer)

        # Then
        mock_temp.write.assert_called_once_with(b"fake_image_data")
        mock_analyze.assert_called_once()
        mock_display.assert_called_once()
        # Check that unlink is called with the correct path (as Path object)
        mock_unlink.assert_called_once()
        call_args = mock_unlink.call_args[0][0]
        assert str(call_args).endswith("test_image.png")

    def test_process_uploaded_file_with_extension(self):
        """Given an uploaded file with extension, When process_uploaded_file is called, Then it should preserve the extension."""
        # Given
        uploaded_file = Mock()
        uploaded_file.name = "test_image.jpg"
        uploaded_file.getvalue.return_value = b"fake_image_data"

        mock_analyzer = Mock()

        # When
        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            mock_temp = Mock()
            mock_temp.name = "/tmp/test_image.jpg"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            with patch("src.pixelguard.streamlit_app.analyze_image"):
                with patch("src.pixelguard.streamlit_app.display_result"):
                    with patch("os.unlink"):
                        process_uploaded_file(uploaded_file, mock_analyzer)

        # Then
        mock_temp_file.assert_called_with(delete=False, suffix=".jpg")


class TestMain:
    """Test suite for the main function."""

    def test_main_function(self):
        """Given the main function is called, When executed, Then it should set up the Streamlit app properly."""
        # Given
        # No specific setup needed

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            with patch(
                "src.pixelguard.streamlit_app.create_analyzer"
            ) as mock_create_analyzer:
                mock_analyzer = Mock()
                mock_create_analyzer.return_value = mock_analyzer

                # Mock file uploader to return no files
                mock_st.file_uploader.return_value = None

                main()

        # Then
        mock_st.set_page_config.assert_called_once()
        mock_st.title.assert_called_once_with("🖼️ PixelGuard")
        mock_st.sidebar.selectbox.assert_called_once()
        mock_st.file_uploader.assert_called_once()
        mock_st.info.assert_called_once_with("Upload images to analyze")

    def test_main_function_with_uploaded_files(self):
        """Given uploaded files, When main function is called, Then it should process the files."""
        # Given
        mock_uploaded_files = [Mock(), Mock()]

        # When
        with patch("src.pixelguard.streamlit_app.st") as mock_st:
            with patch(
                "src.pixelguard.streamlit_app.create_analyzer"
            ) as mock_create_analyzer:
                mock_analyzer = Mock()
                mock_create_analyzer.return_value = mock_analyzer

                # Mock file uploader to return files
                mock_st.file_uploader.return_value = mock_uploaded_files

                with patch(
                    "src.pixelguard.streamlit_app.process_uploaded_file"
                ) as mock_process:
                    main()

        # Then
        mock_create_analyzer.assert_called_once()
        # Should call process_uploaded_file for each uploaded file
        assert mock_process.call_count == 2


class TestStreamlitApp:
    """Test suite for Streamlit app functionality"""

    def test_create_image_analyzer_with_default_detectors(self):
        """Test creating analyzer with default detectors"""
        analyzer = create_image_analyzer()

        # Should have all detectors enabled by default
        assert "border_fill" in analyzer.config.enabled_detectors
        assert "uniform_color" in analyzer.config.enabled_detectors
        assert "background" in analyzer.config.enabled_detectors
        assert "ratio" in analyzer.config.enabled_detectors

    def test_create_image_analyzer_with_custom_detectors(self):
        """Test creating analyzer with custom detector selection"""
        custom_detectors = ["border_fill", "ratio"]
        analyzer = create_image_analyzer(custom_detectors)

        # Should only have specified detectors enabled
        assert analyzer.config.enabled_detectors == custom_detectors

    def test_create_image_analyzer_with_single_detector(self):
        """Test creating analyzer with only one detector enabled"""
        single_detector = ["background"]
        analyzer = create_image_analyzer(single_detector)

        # Should only have background detector enabled
        assert analyzer.config.enabled_detectors == single_detector

    def test_create_image_analyzer_with_no_detectors(self):
        """Test creating analyzer with no detectors enabled"""
        no_detectors = []
        analyzer = create_image_analyzer(no_detectors)

        # Should have empty detector list
        assert analyzer.config.enabled_detectors == no_detectors

    def test_create_image_analyzer_preserves_config_settings(self):
        """Test that custom detector selection preserves other config settings"""
        analyzer = create_image_analyzer(["border_fill"])

        # Should preserve default mode settings for border fill
        assert analyzer.config.border_fill.black_fill_threshold == 0.05
        assert analyzer.config.border_fill.white_fill_threshold == 0.05
        assert analyzer.config.border_fill.uniformity_required == 0.90

        # Should only have border_fill enabled
        assert analyzer.config.enabled_detectors == ["border_fill"]
