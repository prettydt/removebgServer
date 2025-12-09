#!/usr/bin/env python3
"""
Test script to validate the service implementation.
Tests basic functionality without requiring the actual ONNX model.
"""
import os
import sys

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✓ Uvicorn imported successfully")
    except ImportError as e:
        print(f"✗ Uvicorn import failed: {e}")
        return False
    
    try:
        import cv2
        print("✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        import onnxruntime
        print("✓ ONNX Runtime imported successfully")
        print(f"  Available providers: {onnxruntime.get_available_providers()}")
    except ImportError as e:
        print(f"✗ ONNX Runtime import failed: {e}")
        return False
    
    try:
        import prometheus_client
        print("✓ Prometheus client imported successfully")
    except ImportError as e:
        print(f"✗ Prometheus client import failed: {e}")
        return False
    
    return True


def test_app_modules():
    """Test that app modules can be imported."""
    print("\nTesting app modules...")
    
    try:
        from app import auth
        print("✓ app.auth imported successfully")
    except ImportError as e:
        print(f"✗ app.auth import failed: {e}")
        return False
    
    try:
        from app import metrics
        print("✓ app.metrics imported successfully")
    except ImportError as e:
        print(f"✗ app.metrics import failed: {e}")
        return False
    
    try:
        from app import infer
        print("✓ app.infer imported successfully")
    except ImportError as e:
        print(f"✗ app.infer import failed: {e}")
        return False
    
    try:
        from app import main
        print("✓ app.main imported successfully")
    except ImportError as e:
        print(f"✗ app.main import failed: {e}")
        return False
    
    return True


def test_auth_logic():
    """Test authentication logic."""
    print("\nTesting authentication logic...")
    
    from app.auth import get_allowed_keys
    
    # Test with no keys set
    os.environ.pop('ALLOWED_KEYS', None)
    keys = get_allowed_keys()
    if len(keys) == 0:
        print("✓ No keys configured correctly handled")
    else:
        print("✗ Expected empty set when ALLOWED_KEYS not set")
        return False
    
    # Test with keys set
    os.environ['ALLOWED_KEYS'] = 'key1,key2,key3'
    keys = get_allowed_keys()
    if keys == {'key1', 'key2', 'key3'}:
        print("✓ API keys parsed correctly")
    else:
        print(f"✗ Expected {{'key1', 'key2', 'key3'}}, got {keys}")
        return False
    
    # Clean up
    os.environ.pop('ALLOWED_KEYS', None)
    return True


def test_metrics():
    """Test metrics functionality."""
    print("\nTesting metrics...")
    
    from app.metrics import REQUEST_COUNT, ERROR_COUNT, REQUEST_LATENCY
    
    # Test that metrics are defined
    print("✓ Prometheus metrics defined")
    
    # Test incrementing - just verify it doesn't raise an exception
    try:
        REQUEST_COUNT.labels(status='success').inc()
        ERROR_COUNT.labels(error_type='test').inc()
        REQUEST_LATENCY.observe(1.5)
        print("✓ Metrics can be incremented")
    except Exception as e:
        print(f"✗ Metric increment failed: {e}")
        return False
    
    return True


def test_app_creation():
    """Test that FastAPI app can be created."""
    print("\nTesting FastAPI app creation...")
    
    try:
        from app.main import app
        print("✓ FastAPI app created successfully")
        
        # Check routes
        routes = [route.path for route in app.routes]
        expected_routes = ['/health', '/metrics', '/remove-bg']
        
        for route in expected_routes:
            if route in routes:
                print(f"✓ Route {route} exists")
            else:
                print(f"✗ Route {route} not found")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Failed to create app: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Background Removal Service - Implementation Tests")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Run tests
    if not test_imports():
        all_passed = False
        print("\n⚠️  Some dependencies are missing. Install with: pip install -r requirements.txt")
    
    if not test_app_modules():
        all_passed = False
    
    if not test_auth_logic():
        all_passed = False
    
    if not test_metrics():
        all_passed = False
    
    if not test_app_creation():
        all_passed = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All tests passed!")
        print("\nNext steps:")
        print("1. Download the ONNX model (see models/README.md)")
        print("2. Set ALLOWED_KEYS environment variable")
        print("3. Start the server: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
