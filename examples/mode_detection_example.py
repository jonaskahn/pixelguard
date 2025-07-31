#!/usr/bin/env python3
"""
Example script demonstrating mode detection in PixelGuard API

This script shows how to use different detection modes when analyzing images
through the PixelGuard API endpoints.
"""

import requests
import json

# API Configuration
API_BASE_URL = "http://localhost:8000/api"


def get_available_modes():
    """Get list of available detection modes"""
    response = requests.get(f"{API_BASE_URL}/modes")
    if response.status_code == 200:
        return response.json()["modes"]
    return {}


def analyze_file_with_mode(file_path, mode="default"):
    """Analyze a local file with specified detection mode"""
    with open(file_path, 'rb') as f:
        files = {'file': f}
        params = {'mode': mode}
        
        response = requests.post(
            f"{API_BASE_URL}/analyze-files",
            files=files,
            params=params
        )
        
    return response.json() if response.status_code == 200 else None


def analyze_urls_with_mode(urls, mode="default"):
    """Analyze images from URLs with specified detection mode"""
    data = {
        "urls": urls,
        "mode": mode
    }
    
    response = requests.post(
        f"{API_BASE_URL}/analyze-urls",
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    return response.json() if response.status_code == 200 else None


def main():
    """Demonstrate mode detection usage"""
    print("PixelGuard API Mode Detection Example")
    print("=" * 40)
    
    # Get available modes
    print("Available detection modes:")
    modes = get_available_modes()
    for mode, description in modes.items():
        print(f"  {mode}: {description}")
    
    print("\n" + "=" * 40)
    
    # Example 1: File upload with different modes
    print("Example 1: File Upload Analysis")
    print("-" * 30)
    
    # Note: Replace with actual image file path
    example_file = "path/to/your/image.jpg"
    
    for mode in ["strict", "default", "lenient"]:
        print(f"\nAnalyzing with {mode} mode:")
        # result = analyze_file_with_mode(example_file, mode)
        # if result:
        #     print(f"  Result: {result[0]['state']} - {result[0]['detail']}")
        print(f"  curl -X POST '{API_BASE_URL}/analyze-files?mode={mode}' \\")
        print(f"       -F 'file=@{example_file}'")
    
    print("\n" + "=" * 40)
    
    # Example 2: URL analysis with different modes
    print("Example 2: URL Analysis")
    print("-" * 30)
    
    example_urls = [
        "https://example.com/photo.jpg",
        "https://example.com/document.png"
    ]
    
    for mode in ["photo", "document"]:
        print(f"\nAnalyzing URLs with {mode} mode:")
        data = {"urls": example_urls, "mode": mode}
        print(f"  curl -X POST '{API_BASE_URL}/analyze-urls' \\")
        print(f"       -H 'Content-Type: application/json' \\")
        print(f"       -d '{json.dumps(data)}'")
    
    print("\n" + "=" * 40)
    
    # Example 3: Mode-specific use cases
    print("Example 3: Mode-Specific Use Cases")
    print("-" * 30)
    
    use_cases = {
        "strict": "Quality control for professional content",
        "default": "General purpose image validation",
        "lenient": "User-generated content with relaxed standards",
        "photo": "Natural photos and photography",
        "document": "Scanned documents and text images",
        "custom": "Environment-variable configured detection"
    }
    
    for mode, use_case in use_cases.items():
        print(f"  {mode.upper()}: {use_case}")
    
    print("\n" + "=" * 40)
    print("For more information, visit: /api/docs")


if __name__ == "__main__":
    main()
