import os
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

import streamlit as st
from PIL import Image
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pixelguard.analyzers.image import ImageAnalyzer
from src.pixelguard.core.config import DetectionMode, ConfigFactory


def create_image_analyzer(
    enabled_detectors: Optional[List[str]] = None,
) -> ImageAnalyzer:
    """Create image analyzer with specified enabled detectors"""
    config = ConfigFactory.from_mode(DetectionMode.DEFAULT)

    if enabled_detectors is not None:
        from src.pixelguard.core.config import DetectionConfig

        config = DetectionConfig(
            border_fill=config.border_fill,
            uniform_color=config.uniform_color,
            background=config.background,
            ratio=config.ratio,
            enabled_detectors=enabled_detectors,
        )

    return ImageAnalyzer(config)


def analyze_single_image(image_path: Path, analyzer: ImageAnalyzer):
    """Analyze a single image and return analysis result"""
    try:
        return analyzer.analyze(image_path)
    except Exception as e:
        st.error(f"Error analyzing {image_path.name}: {str(e)}")
        return None


def display_detection_result(detection_result, detector_name: str):
    """Display detection result with status and details"""
    status_icon = "🔴" if detection_result.is_problematic else "🟢"
    status_text = "Problematic" if detection_result.is_problematic else "Passed"

    st.write(
        f"{status_icon} **{detector_name}:** "
        f"{status_text} "
        f"(Confidence: {detection_result.confidence:.2f})"
    )

    if detection_result.details:
        with st.expander(f"Details for {detector_name}"):
            for key, value in detection_result.details.items():
                st.write(f"**{key}:** {value}")

    if detection_result.issues:
        with st.expander(f"Issues for {detector_name}"):
            for issue in detection_result.issues:
                st.write(f"• {issue}")


def display_analysis_result(image_path: Path, analysis_result, uploaded_file):
    """Display complete analysis result with image and details"""
    if analysis_result is None:
        return

    with st.container():
        st.markdown("---")
        col1, col2 = st.columns([1, 2])

        with col1:
            display_image(image_path, uploaded_file)

        with col2:
            display_analysis_summary(analysis_result)


def display_image(image_path: Path, uploaded_file):
    """Display uploaded image"""
    try:
        image = Image.open(image_path)
        st.image(image, caption=uploaded_file.name, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading image: {str(e)}")


def display_analysis_summary(analysis_result):
    """Display analysis summary with status and detector results"""
    status = "🔴 PROBLEMATIC" if analysis_result.is_problematic else "🟢 PASSED"
    st.markdown(f"## {status}")
    st.write(f"**Size:** {analysis_result.width} × {analysis_result.height}")

    if analysis_result.detection_results:
        for detection_result in analysis_result.detection_results:
            display_detection_result(detection_result, detection_result.detector_name)


def process_uploaded_file(uploaded_file, analyzer: ImageAnalyzer):
    """Process uploaded file and display analysis results"""
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}"
    ) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_path = Path(temp_file.name)

    analysis_result = analyze_single_image(temp_path, analyzer)
    display_analysis_result(temp_path, analysis_result, uploaded_file)
    os.unlink(temp_path)


def get_enabled_detectors_from_sidebar() -> List[str]:
    """Get list of enabled detectors from sidebar checkboxes"""
    st.sidebar.markdown("### 🔧 Detector Selection")
    st.sidebar.markdown("Enable/disable specific detectors:")

    detector_options = {
        "border_fill": ("Border Fill Detection", "Detect black/white filled borders"),
        "uniform_color": (
            "Uniform Color Detection",
            "Detect images with excessive uniform color",
        ),
        "background": ("Background Detection", "Detect background dominance"),
        "ratio": ("Ratio Detection", "Validate aspect ratios and dimensions"),
    }

    enabled_detectors = []
    for detector_key, (label, help_text) in detector_options.items():
        if st.sidebar.checkbox(label, value=True, help=help_text):
            enabled_detectors.append(detector_key)

    return enabled_detectors


def display_no_detectors_warning():
    """Display warning when no detectors are enabled"""
    st.sidebar.warning("⚠️ No detectors enabled. Please enable at least one detector.")


def display_no_detectors_error():
    """Display error when no detectors are enabled for analysis"""
    st.error(
        "❌ No detectors enabled. Please enable at least one detector to analyze images."
    )


def main():
    """Main Streamlit application"""
    st.set_page_config(page_title="PixelGuard", page_icon="💂🏻", layout="wide")
    st.title("💂🏻 PixelGuard")

    enabled_detectors = get_enabled_detectors_from_sidebar()

    if not enabled_detectors:
        display_no_detectors_warning()

    uploaded_files = st.file_uploader(
        "Upload images",
        type=["png", "jpg", "jpeg", "bmp", "tiff", "webp"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        if not enabled_detectors:
            display_no_detectors_error()
        else:
            analyzer = create_image_analyzer(enabled_detectors)
            for uploaded_file in uploaded_files:
                process_uploaded_file(uploaded_file, analyzer)
    else:
        st.info("Upload images to analyze")


if __name__ == "__main__":
    load_dotenv()
    main()
