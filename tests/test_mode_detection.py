#!/usr/bin/env python3
"""
Test script to verify mode detection functionality in PixelGuard API
"""

import json
import requests
import tempfile
import os
from PIL import Image
import numpy as np

# Test configuration
API_BASE_URL = "http://localhost:8000/api"


def create_test_image():
    """Create a simple test image for analysis"""
    # Create a 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        img.save(tmp.name, 'JPEG')
        return tmp.name


def test_modes_endpoint():
    """Test the /api/modes endpoint"""
    print("Testing /api/modes endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/modes")
        if response.status_code == 200:
            modes = response.json()
            print(f"✓ Available modes: {list(modes['modes'].keys())}")
            return True
        else:
            print(f"✗ Failed to get modes: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing modes endpoint: {e}")
        return False


def test_file_upload_with_mode(mode="default"):
    """Test file upload with specific mode"""
    print(f"Testing file upload with mode: {mode}")
    
    # Create test image
    test_image_path = create_test_image()
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': f}
            params = {'mode': mode}
            
            response = requests.post(
                f"{API_BASE_URL}/analyze-files",
                files=files,
                params=params
            )
            
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Analysis completed with mode '{mode}': {result[0]['state']}")
            return True
        else:
            print(f"✗ Failed analysis with mode '{mode}': {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing file upload with mode '{mode}': {e}")
        return False
    finally:
        # Cleanup
        try:
            os.unlink(test_image_path)
        except:
            pass


def test_url_analysis_with_mode(mode="default"):
    """Test URL analysis with specific mode"""
    print(f"Testing URL analysis with mode: {mode}")
    
    # Use a simple test URL (this would need to be a real image URL in practice)
    test_data = {
        "urls": ["https://via.placeholder.com/150/FF0000/FFFFFF?text=Test"],
        "mode": mode
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze-urls",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ URL analysis completed with mode '{mode}': {result[0]['state']}")
            return True
        else:
            print(f"✗ Failed URL analysis with mode '{mode}': {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing URL analysis with mode '{mode}': {e}")
        return False


def main():
    """Run all tests"""
    print("Starting PixelGuard API Mode Detection Tests")
    print("=" * 50)
    
    # Test modes endpoint
    if not test_modes_endpoint():
        print("Modes endpoint test failed. Make sure the server is running.")
        return
    
    print()
    
    # Test different modes
    test_modes = ["default", "strict", "lenient", "photo", "document"]
    
    for mode in test_modes:
        print(f"\nTesting mode: {mode}")
        print("-" * 30)
        
        # Test file upload
        test_file_upload_with_mode(mode)
        
        # Test URL analysis
        test_url_analysis_with_mode(mode)
    
    print("\n" + "=" * 50)
    print("Tests completed!")


if __name__ == "__main__":
    main()
