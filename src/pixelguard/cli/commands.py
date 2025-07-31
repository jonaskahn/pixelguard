import click

from src.pixelguard import PixelGuard


@click.command("analyze")
@click.argument("image_path", type=click.Path(exists=True))
@click.option(
    "--border-fill-threshold",
    type=float,
    default=0.05,
    help="Border fill threshold percentage (default: 0.05)",
)
@click.option(
    "--uniform-threshold",
    type=float,
    default=0.85,
    help="Uniform color coverage threshold (default: 0.85)",
)
@click.option(
    "--background-threshold",
    type=float,
    default=0.70,
    help="Background dominance threshold (default: 0.70)",
)
@click.option(
    "--color-tolerance",
    type=int,
    default=20,
    help="Color similarity tolerance (default: 20)",
)
@click.option(
    "--ratio-tolerance",
    type=float,
    default=0.1,
    help="Ratio tolerance for aspect ratio matching (default: 0.1)",
)
@click.option(
    "--min-width",
    type=int,
    default=100,
    help="Minimum image width (default: 100)",
)
@click.option(
    "--min-height",
    type=int,
    default=100,
    help="Minimum image height (default: 100)",
)
@click.option(
    "--target-ratios",
    type=str,
    default="16:9,4:3,1:1,3:4,9:16",
    help="Target aspect ratios as comma-separated width:height pairs (default: 16:9,4:3,1:1,3:4,9:16)",
)
def analyze_single_image(
    image_path: str,
    border_fill_threshold: float,
    uniform_threshold: float,
    background_threshold: float,
    color_tolerance: int,
    ratio_tolerance: float,
    min_width: int,
    min_height: int,
    target_ratios: str,
):
    from src.pixelguard.analyzers.image import ImageAnalyzer
    from src.pixelguard.reporters.console_reporter import ConsoleReporter

    detection_config = _build_detection_config_from_cli_options(
        border_fill_threshold=border_fill_threshold,
        uniform_threshold=uniform_threshold,
        background_threshold=background_threshold,
        color_tolerance=color_tolerance,
        ratio_tolerance=ratio_tolerance,
        min_width=min_width,
        min_height=min_height,
        target_ratios=target_ratios,
    )

    image_analyzer = ImageAnalyzer(detection_config)
    single_image_analysis = image_analyzer.analyze(image_path)

    console_reporter = ConsoleReporter(verbose=True)
    console_reporter.report_single(single_image_analysis)


@click.command()
@click.argument("folder_path")
@click.option("--mode", default="photo", help="Detection mode")
@click.option("--format", default="console", help="Output format")
@click.option("--output", default=None, help="Output file")
def analyze_batch(folder_path, mode, format, output):
    pixelguard_analyzer = PixelGuard(mode=mode)
    batch_analysis_report = pixelguard_analyzer.analyze_batch(folder_path)

    batch_reporter = _create_reporter_for_format(format, output)
    batch_reporter.report_batch(batch_analysis_report)


@click.command()
@click.argument("mode", required=False)
def show_config(mode):
    from src.pixelguard.core.config import ConfigFactory, DetectionMode

    if not mode:
        _display_available_modes()
        return

    try:
        mode_config = ConfigFactory.from_mode(DetectionMode(mode.upper()))
        click.echo(mode_config)
    except Exception:
        click.echo(f"Invalid mode: {mode}")


@click.command()
def show_env_vars():
    _display_environment_variables_help()


def _build_detection_config_from_cli_options(
    border_fill_threshold: float,
    uniform_threshold: float,
    background_threshold: float,
    color_tolerance: int,
    ratio_tolerance: float,
    min_width: int,
    min_height: int,
    target_ratios: str,
):
    from src.pixelguard.core.config import (
        DetectionConfig,
        BorderFillConfig,
        UniformColorConfig,
        BackgroundDetectionConfig,
        RatioConfig,
    )

    parsed_ratio_pairs = _parse_target_ratios(target_ratios)

    return DetectionConfig(
        border_fill=BorderFillConfig(
            black_fill_threshold=border_fill_threshold,
            white_fill_threshold=border_fill_threshold,
        ),
        uniform_color=UniformColorConfig(
            uniform_coverage_threshold=uniform_threshold,
            color_delta_threshold=color_tolerance,
        ),
        background=BackgroundDetectionConfig(
            background_coverage_threshold=background_threshold,
            background_color_tolerance=color_tolerance,
        ),
        ratio=RatioConfig(
            tolerance=ratio_tolerance,
            target_ratios=parsed_ratio_pairs,
            minimum_width=min_width,
            minimum_height=min_height,
        ),
    )


def _parse_target_ratios(ratio_string: str):
    parsed_ratio_pairs = []
    for individual_ratio in ratio_string.split(","):
        try:
            width, height = map(float, individual_ratio.strip().split(":"))
            parsed_ratio_pairs.append((width, height))
        except ValueError:
            click.echo(f"Warning: Invalid ratio format '{individual_ratio}', skipping...")
    return parsed_ratio_pairs


def _create_reporter_for_format(output_format: str, output_file_path: str):
    if output_format == "json" and output_file_path:
        from src.pixelguard.reporters.json_reporter import JSONReporter

        return JSONReporter(output_file_path)
    elif output_format == "csv" and output_file_path:
        from src.pixelguard.reporters.csv_reporter import CSVReporter

        return CSVReporter(output_file_path)
    else:
        from src.pixelguard.reporters.console_reporter import ConsoleReporter

        return ConsoleReporter(verbose=True)


def _display_available_modes():
    click.echo("Available modes: strict, default, lenient, photo, document, custom")
    click.echo("\nFor custom mode, set environment variables with PXG_ prefix:")
    click.echo("Example: PXG_BORDER_FILL_BLACK_FILL_THRESHOLD=0.03")


def _display_environment_variables_help():
    click.echo("PixelGuard Custom Configuration Environment Variables")
    click.echo("=" * 60)

    _display_detector_enable_variables()
    _display_border_fill_variables()
    _display_uniform_color_variables()
    _display_background_variables()
    _display_ratio_variables()
    _display_usage_examples()


def _display_detector_enable_variables():
    click.echo("\n🔧 Detector Enable/Disable:")
    click.echo("  PXG_DETECTOR_BORDER_FILL_ENABLED=true")
    click.echo("  PXG_DETECTOR_UNIFORM_COLOR_ENABLED=true")
    click.echo("  PXG_DETECTOR_BACKGROUND_ENABLED=true")
    click.echo("  PXG_DETECTOR_RATIO_ENABLED=true")


def _display_border_fill_variables():
    click.echo("\n📋 Border Fill Detection:")
    click.echo("  PXG_BORDER_FILL_TOP_REGION_PERCENTAGE=0.1")
    click.echo("  PXG_BORDER_FILL_BOTTOM_REGION_PERCENTAGE=0.1")
    click.echo("  PXG_BORDER_FILL_BLACK_THRESHOLD=30")
    click.echo("  PXG_BORDER_FILL_WHITE_THRESHOLD=225")
    click.echo("  PXG_BORDER_FILL_BLACK_FILL_THRESHOLD=0.05")
    click.echo("  PXG_BORDER_FILL_WHITE_FILL_THRESHOLD=0.05")
    click.echo("  PXG_BORDER_FILL_CHECK_TOP=false")
    click.echo("  PXG_BORDER_FILL_CHECK_BOTTOM=true")
    click.echo("  PXG_BORDER_FILL_UNIFORMITY_REQUIRED=0.90")


def _display_uniform_color_variables():
    click.echo("\n🎨 Uniform Color Detection:")
    click.echo("  PXG_UNIFORM_COLOR_DELTA_THRESHOLD=15")
    click.echo("  PXG_UNIFORM_COLOR_SPACE=LAB")
    click.echo("  PXG_UNIFORM_COLOR_COVERAGE_THRESHOLD=0.85")
    click.echo("  PXG_UNIFORM_COLOR_SAMPLE_SIZE=1000")
    click.echo("  PXG_UNIFORM_COLOR_IGNORE_EDGES=true")
    click.echo("  PXG_UNIFORM_COLOR_EDGE_IGNORE_PERCENTAGE=0.02")


def _display_background_variables():
    click.echo("\n🖼️ Background Detection:")
    click.echo("  PXG_BACKGROUND_DETECTION_METHOD=edge_based")
    click.echo("  PXG_BACKGROUND_CORNER_SAMPLE_PERCENTAGE=0.08")
    click.echo("  PXG_BACKGROUND_EDGE_SAMPLE_PERCENTAGE=0.05")
    click.echo("  PXG_BACKGROUND_COVERAGE_THRESHOLD=0.65")
    click.echo("  PXG_BACKGROUND_COLOR_TOLERANCE=25")
    click.echo("  PXG_BACKGROUND_HISTOGRAM_BINS=64")
    click.echo("  PXG_BACKGROUND_DOMINANT_COLOR_THRESHOLD=0.60")


def _display_ratio_variables():
    click.echo("\n📐 Ratio Detection:")
    click.echo("  PXG_RATIO_ENABLED=true")
    click.echo("  PXG_RATIO_TARGET_RATIOS=16:9,4:3,1:1,3:4,9:16")
    click.echo("  PXG_RATIO_TOLERANCE=0.1")
    click.echo("  PXG_RATIO_CHECK_MINIMUM_DIMENSIONS=true")
    click.echo("  PXG_RATIO_MINIMUM_WIDTH=100")
    click.echo("  PXG_RATIO_MINIMUM_HEIGHT=100")
    click.echo("  PXG_RATIO_CHECK_MAXIMUM_DIMENSIONS=false")
    click.echo("  PXG_RATIO_MAXIMUM_WIDTH=10000")
    click.echo("  PXG_RATIO_MAXIMUM_HEIGHT=10000")


def _display_usage_examples():
    click.echo("\n💡 Usage Examples:")
    click.echo("  # Enable only border fill and ratio detectors:")
    click.echo("  export PXG_DETECTOR_BORDER_FILL_ENABLED=true")
    click.echo("  export PXG_DETECTOR_UNIFORM_COLOR_ENABLED=false")
    click.echo("  export PXG_DETECTOR_BACKGROUND_ENABLED=false")
    click.echo("  export PXG_DETECTOR_RATIO_ENABLED=true")
    click.echo(
        "  poetry run python -m src.pixelguard.cli.main batch /path/to/images --mode custom"
    )
    click.echo("")
    click.echo("  # Disable ratio detection:")
    click.echo("  export PXG_DETECTOR_RATIO_ENABLED=false")
    click.echo(
        "  poetry run python -m src.pixelguard.cli.main batch /path/to/images --mode custom"
    )
    click.echo("")
    click.echo("  # Enable all detectors (default):")
    click.echo("  export PXG_DETECTOR_BORDER_FILL_ENABLED=true")
    click.echo("  export PXG_DETECTOR_UNIFORM_COLOR_ENABLED=true")
    click.echo("  export PXG_DETECTOR_BACKGROUND_ENABLED=true")
    click.echo("  export PXG_DETECTOR_RATIO_ENABLED=true")
    click.echo(
        "  poetry run python -m src.pixelguard.cli.main batch /path/to/images --mode custom"
    )
