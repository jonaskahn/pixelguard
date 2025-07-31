from unittest.mock import Mock, patch

import pytest
from sanic_testing import TestManager

from src.pixelguard.server import (
    build_analysis_result,
    download_image_from_url,
    save_uploaded_file,
    analyze_image_file,
    app,
)


class TestBuildAnalysisResult:
    """Test suite for the build_analysis_result function."""

    def test_build_result_with_successful_analysis(self, mock_analysis_result):
        """Given a successful analysis result, When build_result is called, Then it should return pass state."""
        # Given
        file_name = "test_image.png"
        url = "http://example.com/image.png"
        analysis = mock_analysis_result

        # When
        result = build_analysis_result(file_name, url, analysis)

        # Then
        assert result["file_name"] == file_name
        assert result["url"] == url
        assert result["state"] == "pass"
        assert result["detail"] == ""

    def test_build_result_with_problematic_analysis(
        self, mock_problematic_analysis_result
    ):
        """Given a problematic analysis result, When build_result is called, Then it should return failed state."""
        # Given
        file_name = "test_image.png"
        url = "http://example.com/image.png"
        analysis = mock_problematic_analysis_result

        # When
        result = build_analysis_result(file_name, url, analysis)

        # Then
        assert result["file_name"] == file_name
        assert result["url"] == url
        assert result["state"] == "failed"
        assert "border_fill: Too much black border" in result["detail"]

    def test_build_result_with_error(self):
        """Given an error, When build_result is called, Then it should return failed state with error detail."""
        # Given
        file_name = "test_image.png"
        url = "http://example.com/image.png"
        error = "Analysis failed"

        # When
        result = build_analysis_result(file_name, url, None, error=error)

        # Then
        assert result["file_name"] == file_name
        assert result["url"] == url
        assert result["state"] == "failed"
        assert result["detail"] == f"internal error: {error}"

    def test_build_result_with_analysis_issues(self):
        """Given analysis with issues but no detection results, When build_result is called, Then it should include issues in detail."""
        # Given
        file_name = "test_image.png"
        url = "http://example.com/image.png"
        analysis = Mock()
        analysis.is_problematic = True
        analysis.detection_results = []
        analysis.issues = ["General issue detected"]

        # When
        result = build_analysis_result(file_name, url, analysis)

        # Then
        assert result["state"] == "failed"
        assert "unknown: General issue detected" in result["detail"]


class TestDownloadImageFromUrl:
    """Test suite for the download_image_from_url function."""

    @pytest.mark.asyncio
    async def test_download_image_success(self):
        """Given a valid URL, When download_image is called, Then it should download and save the image."""
        # Given
        url = "http://example.com/image.png"

        # When
        with patch("src.pixelguard.server.download_image_from_url") as mock_download:
            mock_download.return_value = ("/tmp/test_image.png", None)

            file_path, error = await download_image_from_url(url)

        # Then
        assert file_path == "/tmp/test_image.png"
        assert error is None

    @pytest.mark.asyncio
    async def test_download_image_http_error(self):
        """Given a URL that returns HTTP error, When download_image is called, Then it should return error."""
        # Given
        url = "http://example.com/image.png"

        # When
        with patch("src.pixelguard.server.download_image_from_url") as mock_download:
            mock_download.return_value = (
                None,
                "Failed to download: http://example.com/image.png (status 404)",
            )

            file_path, error = await download_image_from_url(url)

        # Then
        assert file_path is None
        assert "Failed to download" in error
        assert "status 404" in error

    @pytest.mark.asyncio
    async def test_download_image_network_error(self):
        """Given a network error, When download_image is called, Then it should return error."""
        # Given
        url = "http://example.com/image.png"

        # When
        with patch("src.pixelguard.server.download_image_from_url") as mock_download:
            mock_download.return_value = (None, "Network error")

            file_path, error = await download_image_from_url(url)

        # Then
        assert file_path is None
        assert "Network error" in error


class TestSaveUploadedFile:
    """Test suite for the save_uploaded_file function."""

    def test_save_uploaded_file_success(self, mock_file_upload):
        """Given a valid file upload, When save_uploaded_file is called, Then it should save the file."""
        # Given
        file = mock_file_upload

        # When
        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            mock_temp = Mock()
            mock_temp.name = "/tmp/test_image.png"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            file_path = save_uploaded_file(file)

        # Then
        assert file_path == "/tmp/test_image.png"
        mock_temp.write.assert_called_once_with(file.body)

    def test_save_uploaded_file_with_extension(self):
        """Given a file with extension, When save_uploaded_file is called, Then it should preserve the extension."""
        # Given
        file = Mock()
        file.name = "test_image.jpg"
        file.body = b"fake_image_data"

        # When
        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            mock_temp = Mock()
            mock_temp.name = "/tmp/test_image.jpg"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            file_path = save_uploaded_file(file)

        # Then
        assert file_path == "/tmp/test_image.jpg"
        mock_temp_file.assert_called_with(delete=False, suffix=".jpg")

    def test_save_uploaded_file_exception(self):
        """Given a file that causes an exception, When save_uploaded_file is called, Then it should return None."""
        # Given
        file = Mock()
        file.name = "test_image.png"
        file.body = b"fake_image_data"

        # When
        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            mock_temp_file.side_effect = Exception("File save failed")

            file_path = save_uploaded_file(file)

        # Then
        assert file_path is None


class TestAnalyzeImageFile:
    """Test suite for the analyze_image_file function."""

    @pytest.mark.asyncio
    async def test_analyze_image_file_success(self, sample_image_path):
        """Given a valid image file, When analyze_image_file is called, Then it should return analysis result."""
        # Given
        file_path = sample_image_path
        file_name = "test_image.png"
        url = "http://example.com/image.png"

        # When
        with patch("src.pixelguard.server.PixelGuard") as mock_pixelguard_class:
            mock_guard = Mock()
            mock_analysis = Mock(is_problematic=False)
            mock_guard.analyze_image.return_value = mock_analysis
            mock_pixelguard_class.return_value = mock_guard

            with patch("os.remove") as mock_remove:
                result = await analyze_image_file(file_path, file_name, url)

        # Then
        assert result["file_name"] == file_name
        assert result["url"] == url
        assert result["state"] == "pass"
        mock_guard.analyze_image.assert_called_once_with(file_path)
        mock_remove.assert_called_once_with(file_path)

    @pytest.mark.asyncio
    async def test_analyze_image_file_exception(self, sample_image_path):
        """Given an image file that causes an exception, When analyze_image_file is called, Then it should return error result."""
        # Given
        file_path = sample_image_path
        file_name = "test_image.png"
        url = "http://example.com/image.png"

        # When
        with patch("src.pixelguard.server.PixelGuard") as mock_pixelguard_class:
            mock_guard = Mock()
            mock_guard.analyze_image.side_effect = Exception("Analysis failed")
            mock_pixelguard_class.return_value = mock_guard

            with patch("os.remove") as mock_remove:
                result = await analyze_image_file(file_path, file_name, url)

        # Then
        assert result["file_name"] == file_name
        assert result["url"] == url
        assert result["state"] == "failed"
        assert "internal error: Analysis failed" in result["detail"]
        mock_remove.assert_called_once_with(file_path)

    @pytest.mark.asyncio
    async def test_analyze_image_file_cleanup_failure(self, sample_image_path):
        """Given a file cleanup failure, When analyze_image_file is called, Then it should not raise exception."""
        # Given
        file_path = sample_image_path
        file_name = "test_image.png"
        url = "http://example.com/image.png"

        # When
        with patch("src.pixelguard.server.PixelGuard") as mock_pixelguard_class:
            mock_guard = Mock()
            mock_analysis = Mock(is_problematic=False)
            mock_guard.analyze_image.return_value = mock_analysis
            mock_pixelguard_class.return_value = mock_guard

            with patch("os.remove") as mock_remove:
                mock_remove.side_effect = Exception("Cleanup failed")

                result = await analyze_image_file(file_path, file_name, url)

        # Then
        assert result["state"] == "pass"  # Analysis should still succeed
        mock_remove.assert_called_once_with(file_path)


@pytest.fixture
def client():
    TestManager(app)
    return app.asgi_client


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test the health check endpoint"""
    request, response = await client.get("/api/ping")
    assert response.status == 200
    assert response.text == "pong"


@pytest.mark.asyncio
async def test_api_info_endpoint(client):
    """Test the API info endpoint"""
    response = await client.get("/api/info")
    assert response.status == 200

    data = response.json
    assert data["name"] == "PixelGuard API"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data
    assert "features" in data


@pytest.mark.asyncio
async def test_api_docs_endpoint(client):
    """Test the API docs endpoint"""
    response = await client.get("/api/docs")
    assert response.status == 200

    data = response.json
    assert "message" in data
    assert "swagger_ui" in data
    assert "openapi_spec" in data


@pytest.mark.asyncio
async def test_swagger_ui_endpoint(client):
    """Test that Swagger UI is accessible"""
    response = await client.get("/swagger")
    assert response.status == 200


@pytest.mark.asyncio
async def test_openapi_spec_endpoint(client):
    """Test that OpenAPI specification is accessible"""
    response = await client.get("/openapi/spec.json")
    assert response.status == 200

    spec = response.json
    assert "openapi" in spec
    assert "info" in spec
    assert "paths" in spec
    assert spec["info"]["title"] == "PixelGuard API"


@pytest.mark.asyncio
async def test_analyze_files_no_files(client):
    """Test analyze files endpoint with no files"""
    response = await client.post("/api/analyze-files")
    assert response.status == 400

    data = response.json
    assert data["status_code"] == 400
    assert data["message"] == "No files provided"


@pytest.mark.asyncio
async def test_analyze_urls_no_urls(client):
    """Test analyze URLs endpoint with no URLs"""
    response = await client.post("/api/analyze-urls")
    assert response.status == 400

    data = response.json
    assert data["status_code"] == 400
    assert data["message"] == "No urls provided"


@pytest.mark.asyncio
async def test_analyze_urls_with_urls(client):
    """Test analyze URLs endpoint with valid URLs"""
    response = await client.post(
        "/api/analyze-urls", json={"urls": ["https://example.com/test.jpg"]}
    )
    assert response.status == 200

    data = response.json
    assert isinstance(data, list)
    assert len(data) == 1
    assert "file_name" in data[0]
    assert "url" in data[0]
    assert "state" in data[0]
    assert "detail" in data[0]
