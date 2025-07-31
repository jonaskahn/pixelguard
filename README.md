# 💂🏻 PixelGuard

A sophisticated image analysis tool that detects problematic images with advanced color analysis and border detection.

## 🎯 Features

### **Four Specialized Detection Types**

1. **Border Fill Detection** - Detects black/white filled borders at image edges
2. **Uniform Color Detection** - Identifies images that are mostly the same color
3. **Background Dominance Detection** - Finds images where background color dominates
4. **Ratio Detection** - Validates image aspect ratios and dimensions

### **Advanced Color Analysis**

- Multiple color spaces (RGB, HSV, LAB)
- Machine learning-based color clustering
- Configurable color similarity thresholds
- Edge and corner-based background detection

### **Flexible Configuration**

- Four preset modes: Strict, Lenient, Photo, Document
- Custom threshold configuration
- Granular control over detection parameters
- Easy to extend with new detection methods

### **Web Interface**

- **Streamlit UI** - Beautiful web interface for easy image analysis
- **Multi-image upload** - Upload and analyze multiple images at once
- **Real-time results** - See analysis results immediately
- **Interactive details** - Expandable sections for detailed information

## 🚀 Quick Start

### **Installation**

```bash
# Clone the repository
git clone <repository-url>
cd pixelguard

# Install dependencies
poetry install
```

### **Web Interface (Recommended)**

```bash
# Start the Streamlit web interface
streamlit run src/pixelguard/streamlit_app.py
```

The web interface will open at `http://localhost:8501` and provides:

- Easy image upload with drag-and-drop
- Detection mode selection
- Real-time analysis results
- Detailed breakdown of issues

### **Python API Usage**

```python
from src.pixelguard.analyzers.image import ImageAnalyzer
from src.pixelguard import DetectionMode, ConfigFactory

# Create analyzer with default mode
analyzer = ImageAnalyzer(ConfigFactory.from_mode(DetectionMode.DEFAULT))

# Analyze a single image
result = analyzer.analyze("image.jpg")
print(f"Problematic: {result.is_problematic}")
```

### **CLI Usage**

```bash
# Analyze single image
poetry run python -m src.pixelguard.cli.main check image.jpg --mode strict

# Analyze with custom ratio settings
poetry run python -m src.pixelguard.cli.main analyze image.jpg \
  --ratio-tolerance 0.05 \
  --min-width 200 \
  --min-height 200 \
  --target-ratios "16:9,4:3,1:1"

# Custom mode with environment variables
export PXG_BORDER_FILL_BLACK_FILL_THRESHOLD=0.03
export PXG_RATIO_TOLERANCE=0.05
export PXG_RATIO_TARGET_RATIOS=16:9,4:3,1:1
poetry run python -m src.pixelguard.cli.main batch /path/to/images --mode custom

# Enable/disable specific detectors
export PXG_DETECTOR_BORDER_FILL_ENABLED=true
export PXG_DETECTOR_UNIFORM_COLOR_ENABLED=false
export PXG_DETECTOR_BACKGROUND_ENABLED=true
export PXG_DETECTOR_RATIO_ENABLED=false
poetry run python -m src.pixelguard.cli.main batch /path/to/images --mode custom

# Show available environment variables
poetry run python -m src.pixelguard.cli.main show-env-vars

# Batch processing
poetry run python -m src.pixelguard.cli.main batch /path/to/images --mode photo
```

### **API Usage**

The PixelGuard API provides RESTful endpoints for image analysis:

#### **Health Check**

```bash
curl http://localhost:8000/api/health
```

#### **Analyze Uploaded Files**

```bash
curl -X POST http://localhost:8000/api/analyze-files \
  -F "files=@image1.jpg" \
  -F "files=@image2.png"
```

#### **Analyze Images from URLs**

```bash
curl -X POST http://localhost:8000/api/analyze-urls \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.png"
    ]
  }'
```

#### **API Documentation**

- **API Information**: http://localhost:8000/api/info

The API supports:

- **File Upload**: Multipart form data with multiple image files
- **URL Analysis**: JSON payload with image URLs
- **Multiple Formats**: JPG, JPEG, PNG, BMP, TIFF
- **Batch Processing**: Analyze multiple images in a single request
- **Detailed Results**: Comprehensive analysis with issue descriptions

## 🐳 Docker

### **Quick Start with Docker**

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### **Access Services**

- **API**: http://localhost:8000/api/health
- **API Info**: http://localhost:8000/api/info
- **Streamlit UI**: http://localhost:8501

### **Docker Commands**

```bash
# Start services
docker-compose up

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild and restart
docker-compose up --build
```

### **Manual Docker Build**

```bash
# Build image
docker build -t jonaskahn/pixelguard .

# Run container
docker run --rm -p 8000:8000 -p 8501:8501 jonaskahn/pixelguard
```

## 📋 Detection Modes

### **Strict Mode**

- Very low thresholds for all detectors
- 3% border fill threshold
- 80% uniform color coverage
- 65% background coverage
- 5% ratio tolerance
- Minimum 200x200 dimensions

### **Default Mode**

- Balanced thresholds for general use
- 5% border fill threshold
- 85% uniform color coverage
- 70% background coverage
- 10% ratio tolerance
- Minimum 100x100 dimensions

### **Lenient Mode**

- Higher thresholds for all detectors
- 15% border fill threshold
- 95% uniform color coverage
- 85% background coverage
- 20% ratio tolerance
- Minimum 50x50 dimensions

### **Photo Mode**

- Optimized for photographic images
- Smaller border regions (5%)
- LAB color space for better color analysis
- Edge-based background detection
- 10% ratio tolerance
- Minimum 300x300 dimensions

### **Document Mode**

- Optimized for document images
- Very strict border detection (2%)
- RGB color space
- Histogram-based background detection
- 5% ratio tolerance
- Minimum 500x500 dimensions

### **Custom Mode**

- Fully configurable via environment variables
- All parameters customizable with `PXG_` prefix
- Perfect for containerized deployments
- Supports dynamic configuration without code changes

## 🔧 Configuration

### **Custom Configuration**

```python
from src.pixelguard import DetectionConfig, BorderFillConfig, UniformColorConfig, BackgroundDetectionConfig, RatioConfig
from src.pixelguard.analyzers.image import ImageAnalyzer

# Create custom configuration
config = DetectionConfig(
    border_fill=BorderFillConfig(
        black_fill_threshold=0.03,  # 3% threshold
        white_fill_threshold=0.03,
        uniformity_required=0.95  # 95% uniformity required
    ),
    uniform_color=UniformColorConfig(
        uniform_coverage_threshold=0.80,  # 80% uniform coverage
        color_delta_threshold=10,  # Stricter color tolerance
        color_space="LAB"  # Use LAB color space
    ),
    background=BackgroundDetectionConfig(
        background_coverage_threshold=0.65,  # 65% background coverage
        background_color_tolerance=15,  # Stricter tolerance
        detection_method="edge_based"  # Use edge-based detection
    ),
    ratio=RatioConfig(
        tolerance=0.05,  # 5% ratio tolerance
        target_ratios=[(16, 9), (4, 3), (1, 1)],  # Common ratios
        minimum_width=200,  # Minimum width
        minimum_height=200,  # Minimum height
        check_maximum_dimensions=True,  # Enable max dimension check
        maximum_width=4000,  # Maximum width
        maximum_height=4000  # Maximum height
    )
)

analyzer = ImageAnalyzer(config)
result = analyzer.analyze("image.jpg")
```

### **Environment Variable Configuration**

For containerized deployments or dynamic configuration, use the `custom` mode with environment variables:

```bash
# Set environment variables
export PXG_BORDER_FILL_BLACK_FILL_THRESHOLD=0.03
export PXG_RATIO_TOLERANCE=0.05
export PXG_RATIO_TARGET_RATIOS=16:9,4:3,1:1

# Use custom mode
poetry run python -m src.pixelguard.cli.main batch /path/to/images --mode custom
```

**Available Environment Variables:**

- **Detector Enable/Disable**: `PXG_DETECTOR_*_ENABLED`
- **Border Fill**: `PXG_BORDER_FILL_*`
- **Uniform Color**: `PXG_UNIFORM_COLOR_*`
- **Background**: `PXG_BACKGROUND_*`
- **Ratio**: `PXG_RATIO_*`

Run `poetry run python -m src.pixelguard.cli.main show-env-vars` to see all available variables.

### **Detector Enable/Disable**

In custom mode, you can enable or disable individual detectors using environment variables:

```bash
# Enable only border fill and background detection
export PXG_DETECTOR_BORDER_FILL_ENABLED=true
export PXG_DETECTOR_UNIFORM_COLOR_ENABLED=false
export PXG_DETECTOR_BACKGROUND_ENABLED=true
export PXG_DETECTOR_RATIO_ENABLED=false

# Disable ratio detection only
export PXG_DETECTOR_RATIO_ENABLED=false
```

**Supported Boolean Values:**

- `true`, `1`, `yes`, `on` → Enabled
- `false`, `0`, `no`, `off` → Disabled
- Invalid values default to `true`

## 🏗️ Architecture

### **Core Components**

- **ImageAnalyzer**: Main analysis orchestrator
- **BorderFillDetector**: Detects black/white filled borders
- **UniformColorDetector**: Identifies uniform color images
- **BackgroundDetector**: Detects background dominance
- **RatioDetector**: Validates aspect ratios and dimensions
- **CompositeDetector**: Combines multiple detectors
- **ConfigFactory**: Creates preset configurations

### **Detection Architecture**

#### 1. **Border Fill Detection**

- Analyzes top and bottom regions of images
- Detects black/white filled borders
- Configurable region percentages and thresholds

#### 2. **Uniform Color Detection**

- Samples pixels across the image
- Uses multiple color spaces (RGB, HSV, LAB)
- Detects images with excessive uniform color

#### 3. **Background Dominance Detection**

- Multiple detection methods (edge-based, corner-based, histogram)
- Identifies dominant background colors
- Configurable coverage thresholds

#### 4. **Ratio Detection**

- Validates image aspect ratios against target ratios
- Checks minimum and maximum dimensions
- Configurable tolerance for ratio matching
- Supports multiple target ratios (16:9, 4:3, 1:1, etc.)

### **Configuration System**

- **DetectionConfig**: Main configuration container
- **BorderFillConfig**: Border detection parameters
- **UniformColorConfig**: Color uniformity settings
- **BackgroundDetectionConfig**: Background analysis options
- **RatioConfig**: Aspect ratio and dimension validation settings

## 📊 Output Format

The system provides detailed detection results as Python objects:

```python
# ImageAnalysis object returned by analyzer.analyze()
{
    "file_path": "image.jpg",
    "width": 1920,
    "height": 1080,
    "detection_results": [
        {
            "detector_name": "border_fill",
            "is_problematic": True,
            "confidence": 0.85,
            "details": {
                "top_border": {
                    "black_percentage": 0.08,
                    "white_percentage": 0.02,
                    "is_problematic": True
                }
            },
            "issues": ["Top border has black fill: 8.0%"]
        },
        {
            "detector_name": "uniform_color",
            "is_problematic": False,
            "confidence": 0.42,
            "details": {
                "dominant_color": [128, 130, 125],
                "uniformity_percentage": 0.42,
                "color_space": "LAB",
                "sample_size": 1000
            },
            "issues": []
        },
        {
            "detector_name": "ratio",
            "is_problematic": True,
            "confidence": 0.5,
            "details": {
                "width": 1920,
                "height": 1080,
                "current_ratio": 1.778,
                "target_ratios": [(16, 9), (4, 3), (1, 1)],
                "tolerance": 0.05,
                "ratio_issues": ["Ratio 1.778 doesn't match any target ratios. Closest: 1.778 (16:9)"],
                "dimension_issues": []
            },
            "issues": ["Ratio 1.778 doesn't match any target ratios. Closest: 1.778 (16:9)"]
        }
    ],
    "is_problematic": True
}
```

### **Data Models**

- **ImageAnalysis**: Contains image metadata and detection results
- **DetectionResult**: Individual detector result with confidence and details
- **BatchReport**: Summary of multiple image analyses

## 🔬 Technical Details

### **Dependencies**

- `opencv-python`: Image processing and analysis
- `scikit-learn`: Machine learning for color clustering
- `streamlit`: Web interface framework
- `PIL`: Image handling
- `rich`: Beautiful terminal output
- `click`: Command-line interface framework

### **Color Spaces**

- **RGB**: Standard color space, good for documents
- **HSV**: Hue-Saturation-Value, good for color-based analysis
- **LAB**: Perceptually uniform, excellent for photos

### **Detection Methods**

- **Edge-based**: Samples from image edges to detect background
- **Corner-based**: Samples from image corners to detect background
- **Histogram-based**: Uses color histogram to find dominant colors

## 🧪 Testing

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/pixelguard
```

## 📚 Documentation

The codebase includes comprehensive documentation in the source code and this README.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Benefits

1. **More Precise Detection**: Specific detection for actual use cases
2. **Advanced Color Analysis**: Multiple color spaces and clustering
3. **Flexible Configuration**: Fine-tuned presets and custom options
4. **Better User Experience**: Web interface and clear, actionable issue descriptions
5. **Extensible Architecture**: Easy to add new detection methods
