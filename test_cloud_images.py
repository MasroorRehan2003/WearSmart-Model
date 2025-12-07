"""
Test script for WearSmart FastAPI endpoints
Tests the /health and /cloud-images endpoints to verify API + MongoDB + Cloudinary integration

Usage:
    python test_cloud_images.py

Prerequisites:
    - FastAPI server must be running on http://127.0.0.1:8000
    - Start server with: uvicorn wearsmart_api:app --reload --port 8000
"""

import json
import requests
from typing import Optional

BASE_URL = "http://127.0.0.1:8000"


def print_response(label: str, response: requests.Response) -> None:
    """Print formatted response with status code and JSON body"""
    print(f"\n{label}")
    print("-" * 60)
    print(f"Status Code: {response.status_code}")
    
    try:
        json_data = response.json()
        print("Response Body:")
        print(json.dumps(json_data, indent=2))
    except json.JSONDecodeError:
        print("Response Body (not JSON):")
        print(response.text)
    print("-" * 60)


def test_health() -> bool:
    """Test the /health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print_response("--- HEALTH ---", response)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("\n--- HEALTH ---")
        print("-" * 60)
        print("❌ Connection Error!")
        print("Server not running on 127.0.0.1:8000 – please start uvicorn first.")
        print("Run: uvicorn wearsmart_api:app --reload --port 8000")
        print("-" * 60)
        return False
    except Exception as e:
        print("\n--- HEALTH ---")
        print("-" * 60)
        print(f"❌ Error: {e}")
        print("-" * 60)
        return False


def test_cloud_images(gender: str, label: str, limit: int = 5) -> bool:
    """Test the /cloud-images endpoint"""
    try:
        params = {
            "gender": gender,
            "label": label,
            "limit": limit
        }
        response = requests.get(
            f"{BASE_URL}/cloud-images",
            params=params,
            timeout=10
        )
        
        label_text = f"--- {gender.upper()} {label.upper()} CLOUD IMAGES ---"
        print_response(label_text, response)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        label_text = f"--- {gender.upper()} {label.upper()} CLOUD IMAGES ---"
        print(f"\n{label_text}")
        print("-" * 60)
        print("❌ Connection Error!")
        print("Server not running on 127.0.0.1:8000 – please start uvicorn first.")
        print("Run: uvicorn wearsmart_api:app --reload --port 8000")
        print("-" * 60)
        return False
    except Exception as e:
        label_text = f"--- {gender.upper()} {label.upper()} CLOUD IMAGES ---"
        print(f"\n{label_text}")
        print("-" * 60)
        print(f"❌ Error: {e}")
        print("-" * 60)
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 WearSmart API Test Suite")
    print("Testing FastAPI + MongoDB + Cloudinary Integration")
    print("=" * 60)
    
    # Test health endpoint
    health_ok = test_health()
    
    if not health_ok:
        print("\n❌ Health check failed. Cannot proceed with other tests.")
        print("Please ensure the server is running and try again.")
        return
    
    # Test cloud-images endpoints
    print("\n")
    test_cloud_images("men", "hoodie", limit=5)
    
    print("\n")
    test_cloud_images("women", "tops", limit=5)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

