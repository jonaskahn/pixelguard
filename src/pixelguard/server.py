import os
import platform
import tempfile
from json import dumps

import aiohttp
from sanic import Sanic, Request
from sanic import json, text
from sanic.log import logger
from sanic.request import File
from sanic.worker.manager import WorkerManager
from sanic_cors import CORS

from src.pixelguard import PixelGuard

app = Sanic("PixelGuard-API", dumps=dumps)

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


def build_analysis_result(file_name, url, analysis, error=None):
    """Build standardized analysis result response"""
    if error:
        return {
            "file_name": file_name,
            "url": url,
            "state": "failed",
            "detail": f"internal error: {error}",
        }

    is_problematic = getattr(analysis, "is_problematic", False)
    state = "failed" if is_problematic else "pass"
    detail = _extract_detection_details(analysis) if is_problematic else ""

    return {
        "file_name": file_name,
        "url": url,
        "state": state,
        "detail": detail,
    }


def _extract_detection_details(analysis):
    """Extract detailed detection information from analysis result"""
    detector_details = []

    if hasattr(analysis, "detection_results"):
        for result in analysis.detection_results:
            if getattr(result, "is_problematic", False) and getattr(
                result, "issues", []
            ):
                detector_name = getattr(result, "detector_name", "detector")
                for issue in result.issues:
                    detector_details.append(f"{detector_name}: {issue}")

    if not detector_details and hasattr(analysis, "issues") and analysis.issues:
        for issue in analysis.issues:
            detector_details.append(f"unknown: {issue}")

    return "; ".join(detector_details) if detector_details else "failed by detector(s)"


async def download_image_from_url(url):
    """Download image from URL and return temporary file path"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to download: {url} (status {response.status})"
                    )

                suffix = os.path.splitext(url)[-1] or ".jpg"
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix
                ) as temp_file:
                    temp_file.write(await response.read())
                    return temp_file.name, None
    except Exception as e:
        return None, str(e)


def save_uploaded_file(file: File):
    """Save uploaded file to temporary location"""
    try:
        suffix = os.path.splitext(file.name)[-1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file.body)
            return temp_file.name
    except Exception:
        return None


async def analyze_image_file(file_path, file_name, url=None):
    """Analyze image file and return result"""
    guard = PixelGuard()
    try:
        analysis = guard.analyze_image(file_path)
        return build_analysis_result(file_name, url, analysis)
    except Exception as e:
        return build_analysis_result(file_name, url, None, error=e)
    finally:
        _cleanup_temp_file(file_path)


def _cleanup_temp_file(file_path):
    """Clean up temporary file"""
    try:
        os.remove(file_path)
    except Exception:
        pass


@app.exception(Exception)
async def handle_exception(request: Request, exception: Exception):
    """Handle unhandled exceptions"""
    logger.error(exception, exc_info=True)
    return json(
        {"message": str(exception)},
        status=500,
    )


@app.get("/api/ping")
async def health_check(request: Request):
    """Check API health status"""
    return text("pong")


@app.post("/api/analyze-files")
async def analyze_uploaded_files(request: Request):
    """Analyze uploaded image files for quality issues"""
    files = _extract_uploaded_files(request)

    if not files:
        return json({"status_code": 400, "message": "No files provided"}, status=400)

    results = []
    for file in files:
        result = await _process_uploaded_file(file)
        results.append(result)

    return json(results, status=200)


def _extract_uploaded_files(request: Request):
    """Extract uploaded files from request"""
    upload_files = list(request.files.values()) if request.files else []
    return [item for sublist in upload_files for item in sublist]


async def _process_uploaded_file(file):
    """Process a single uploaded file"""
    file_path = save_uploaded_file(file)
    if not file_path:
        return build_analysis_result(file.name, None, None, error="Failed to save file")

    return await analyze_image_file(file_path, file.name)


@app.post("/api/analyze-urls")
async def analyze_images_from_urls(request: Request):
    """Analyze images from URLs for quality issues"""
    urls = _extract_urls_from_request(request)

    if not urls:
        return json({"status_code": 400, "message": "No urls provided"}, status=400)

    results = []
    for url in urls:
        result = await _process_url_image(url)
        results.append(result)

    return json(results, status=200)


def _extract_urls_from_request(request: Request):
    """Extract URLs from request body"""
    urls = []
    if request.content_type and "application/json" in request.content_type:
        try:
            data = request.json or {}
            if isinstance(data, dict) and "urls" in data:
                urls = data["urls"]
            elif isinstance(data, list):
                urls = data
        except Exception:
            pass
    return urls


async def _process_url_image(url):
    """Process a single URL image"""
    file_path, error = await download_image_from_url(url)
    if not file_path:
        return build_analysis_result(os.path.basename(url), url, None, error=error)

    return await analyze_image_file(file_path, os.path.basename(url), url=url)


if __name__ == "__main__":
    debug_mode = os.getenv("PXG_DEBUG", "false").lower() == "true"
    workers = int(os.getenv("PXG_WORKERS", "10"))

    app.run(
        host="0.0.0.0",
        port=8000,
        access_log=True,
        verbosity=1 if debug_mode else 0,
        dev=debug_mode,
        debug=debug_mode,
        workers=workers,
    )
