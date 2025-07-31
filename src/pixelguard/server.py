import os
import platform
import tempfile
from json import dumps
from typing import List

import aiohttp
from dotenv import load_dotenv
from sanic import Sanic, Request
from sanic import json, text
from sanic.log import logger
from sanic.request import File
from sanic.worker.manager import WorkerManager
from sanic_cors import CORS
from sanic_ext import Extend, openapi

from pixelguard import PixelGuard

app = Sanic("PixelGuard-API", dumps=dumps)

Extend(app)

app.ext.openapi.describe(
    "PixelGuard API",
    version="1.0.0",
    description="A sophisticated image analysis API that detects problematic images with advanced color analysis and border detection.",
)

app.config.KEEP_ALIVE = False
app.config.REQUEST_TIMEOUT = 6000
app.config.RESPONSE_TIMEOUT = 6000
CORS(app)
WorkerManager.THRESHOLD = 600

if platform.system() == "Linux":
    logger.debug('use "fork" for multi-process')
    Sanic.start_method = "fork"
else:
    logger.debug('use "spawn" for multi-process')

from dataclasses import dataclass
from typing import Optional


@dataclass
class AnalysisResult:
    file_name: str
    state: str
    detail: str
    url: Optional[str] = None


@dataclass
class ErrorResponse:
    status_code: int
    message: str


@dataclass
class URLListRequest:
    urls: List[str]
    mode: Optional[str] = "default"


def build_analysis_result(file_name, url, analysis, error=None):
    if error:
        return {
            "file_name": file_name,
            "url": url,
            "state": "failed",
            "detail": f"internal error: {error}",
        }

    has_issues = getattr(analysis, "is_problematic", False)
    result_state = "failed" if has_issues else "pass"
    issue_details = _extract_detection_details(analysis) if has_issues else ""

    return {
        "file_name": file_name,
        "url": url,
        "state": result_state,
        "detail": issue_details,
    }


def _extract_detection_details(analysis):
    issue_descriptions = []

    if hasattr(analysis, "detection_results"):
        for detection_result in analysis.detection_results:
            if getattr(detection_result, "is_problematic", False) and getattr(
                detection_result, "issues", []
            ):
                detector_name = getattr(detection_result, "detector_name", "detector")
                for issue in detection_result.issues:
                    issue_descriptions.append(f"{detector_name}: {issue}")

    if not issue_descriptions and hasattr(analysis, "issues") and analysis.issues:
        for issue in analysis.issues:
            issue_descriptions.append(f"unknown: {issue}")

    return (
        "; ".join(issue_descriptions) if issue_descriptions else "failed by detector(s)"
    )


async def download_image_from_url(image_url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to download: {image_url} (status {response.status})"
                    )

                file_extension = os.path.splitext(image_url)[-1] or ".jpg"
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=file_extension
                ) as temp_file:
                    temp_file.write(await response.read())
                    return temp_file.name, None
    except Exception as e:
        return None, str(e)


def save_uploaded_file(uploaded_file: File):
    try:
        file_extension = os.path.splitext(uploaded_file.name)[-1] or ".jpg"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            temp_file.write(uploaded_file.body)
            return temp_file.name
    except Exception:
        return None


async def analyze_image_file(file_path, file_name, url=None, detection_mode="default"):
    pixelguard_analyzer = PixelGuard(mode=detection_mode)
    try:
        analysis_result = pixelguard_analyzer.analyze_image(file_path)
        return build_analysis_result(file_name, url, analysis_result)
    except Exception as e:
        return build_analysis_result(file_name, url, None, error=e)
    finally:
        _cleanup_temp_file(file_path)


def _cleanup_temp_file(file_path):
    try:
        os.remove(file_path)
    except Exception:
        pass


def _validate_and_get_mode(mode_parameter):
    supported_modes = ["strict", "default", "lenient", "photo", "document", "custom"]

    if mode_parameter is None:
        return "default"

    normalized_mode = mode_parameter.lower()
    if normalized_mode in supported_modes:
        return normalized_mode

    return "default"


@app.exception(Exception)
async def handle_exception(request: Request, exception: Exception):
    logger.error(exception, exc_info=True)
    return json(
        {"message": str(exception)},
        status=500,
    )


@app.get("/api/ping")
@openapi.summary("Health Check")
@openapi.description("Check if the PixelGuard API is running and responsive")
@openapi.response(200, str, description="Returns 'pong' if the service is healthy")
@openapi.tag("Health")
async def health_check(request: Request):
    return text("pong")


@app.get("/api/modes")
@openapi.summary("Get Available Detection Modes")
@openapi.description("Get list of available detection modes with their descriptions")
@openapi.response(200, dict, description="List of available detection modes")
@openapi.tag("Configuration")
async def get_detection_modes(request: Request):
    modes = {
        "strict": "Strict detection with low tolerance for issues",
        "default": "Balanced detection suitable for most use cases",
        "lenient": "Lenient detection with high tolerance for minor issues",
        "photo": "Optimized for photo analysis with natural image characteristics",
        "document": "Optimized for document analysis with text and structured content",
        "custom": "Custom configuration based on environment variables",
    }
    return json({"modes": modes}, status=200)


@app.post("/api/analyze-files")
@openapi.summary("Analyze Uploaded Image Files")
@openapi.description(
    "Upload and analyze image files for quality issues including color uniformity, border fills, and aspect ratio problems. "
    "Supports detection modes: strict, default, lenient, photo, document, custom"
)
@openapi.parameter(
    "mode",
    str,
    "query",
    description="Detection mode (strict, default, lenient, photo, document, custom). Defaults to 'default'",
)
@openapi.response(
    200, List[AnalysisResult], description="Successfully analyzed all files"
)
@openapi.response(
    400, ErrorResponse, description="No files provided or invalid request"
)
@openapi.response(
    500, ErrorResponse, description="Internal server error during analysis"
)
@openapi.tag("Image Analysis")
async def analyze_uploaded_files(request: Request):
    uploaded_files = _extract_uploaded_files(request)

    if not uploaded_files:
        return json({"status_code": 400, "message": "No files provided"}, status=400)

    detection_mode = _validate_and_get_mode(request.args.get("mode"))

    analysis_results = []
    for uploaded_file in uploaded_files:
        analysis_result = await _process_uploaded_file(uploaded_file, detection_mode)
        analysis_results.append(analysis_result)

    return json(analysis_results, status=200)


def _extract_uploaded_files(request: Request):
    file_lists = list(request.files.values()) if request.files else []
    return [uploaded_file for file_list in file_lists for uploaded_file in file_list]


async def _process_uploaded_file(uploaded_file, detection_mode="default"):
    temp_file_path = save_uploaded_file(uploaded_file)
    if not temp_file_path:
        return build_analysis_result(
            uploaded_file.name, None, None, error="Failed to save file"
        )

    return await analyze_image_file(
        temp_file_path, uploaded_file.name, detection_mode=detection_mode
    )


@app.post("/api/analyze-urls")
@openapi.summary("Analyze Images from URLs")
@openapi.description(
    "Download and analyze images from provided URLs for quality issues including color uniformity, border fills, and aspect ratio problems. "
    "Supports detection modes: strict, default, lenient, photo, document, custom"
)
@openapi.body(
    URLListRequest,
    description="JSON object containing list of image URLs and optional detection mode",
)
@openapi.response(
    200, List[AnalysisResult], description="Successfully analyzed all images from URLs"
)
@openapi.response(400, ErrorResponse, description="No URLs provided or invalid request")
@openapi.response(
    500, ErrorResponse, description="Internal server error during analysis"
)
@openapi.tag("Image Analysis")
async def analyze_images_from_urls(request: Request):
    image_urls, detection_mode = _extract_urls_and_mode_from_request(request)

    if not image_urls:
        return json({"status_code": 400, "message": "No urls provided"}, status=400)

    analysis_results = []
    for image_url in image_urls:
        analysis_result = await _process_url_image(image_url, detection_mode)
        analysis_results.append(analysis_result)

    return json(analysis_results, status=200)


def _extract_urls_from_request(request: Request):
    image_urls = []
    if request.content_type and "application/json" in request.content_type:
        try:
            request_data = request.json or {}
            if isinstance(request_data, dict) and "urls" in request_data:
                image_urls = request_data["urls"]
            elif isinstance(request_data, list):
                image_urls = request_data
        except Exception:
            pass
    return image_urls


def _extract_urls_and_mode_from_request(request: Request):
    image_urls = []
    detection_mode = "default"

    if request.content_type and "application/json" in request.content_type:
        try:
            request_data = request.json or {}
            if isinstance(request_data, dict):
                if "urls" in request_data:
                    image_urls = request_data["urls"]
                if "mode" in request_data:
                    detection_mode = _validate_and_get_mode(request_data["mode"])
            elif isinstance(request_data, list):
                image_urls = request_data
        except Exception:
            pass

    return image_urls, detection_mode


async def _process_url_image(image_url, detection_mode="default"):
    temp_file_path, download_error = await download_image_from_url(image_url)
    if not temp_file_path:
        return build_analysis_result(
            os.path.basename(image_url), image_url, None, error=download_error
        )

    return await analyze_image_file(
        temp_file_path,
        os.path.basename(image_url),
        url=image_url,
        detection_mode=detection_mode,
    )


if __name__ == "__main__":
    load_dotenv()
    debug_mode = os.getenv("PXG_DEBUG", "false").lower() == "true"
    workers = int(os.getenv("PXG_WORKERS", "20"))

    app.run(
        host="0.0.0.0",
        port=8000,
        access_log=True,
        verbosity=1 if debug_mode else 0,
        dev=debug_mode,
        debug=debug_mode,
        workers=workers,
    )
