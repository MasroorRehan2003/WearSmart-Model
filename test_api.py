"""
Quick test script for WearSmart FastAPI
Run this after starting the server to verify everything works
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed!")
            print(f"   Men model loaded: {data.get('men_model_loaded', False)}")
            print(f"   Women model loaded: {data.get('women_model_loaded', False)}")
            print(f"   Men images available: {data.get('men_static', False)}")
            print(f"   Women images available: {data.get('women_static', False)}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        print("   Make sure the server is running!")
        return False

def test_men_recommendation():
    """Test men's recommendation endpoint"""
    print("\n🔍 Testing /recommend/men endpoint...")
    try:
        payload = {
            "temperature": 25.0,
            "feels_like": 27.0,
            "humidity": 65.0,
            "wind_speed": 10.0,
            "weather_condition": "clear",
            "time_of_day": "morning",
            "season": "summer",
            "mood": "Neutral",
            "occasion": "casual"
        }
        response = requests.post(
            f"{BASE_URL}/recommend/men",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Men's recommendation successful!")
            print(f"   Top: {data.get('top')}")
            print(f"   Bottom: {data.get('bottom')}")
            print(f"   Outer: {data.get('outer')}")
            return data
        else:
            print(f"❌ Recommendation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Recommendation error: {e}")
        return None

def test_women_recommendation():
    """Test women's recommendation endpoint"""
    print("\n🔍 Testing /recommend/women endpoint...")
    try:
        payload = {
            "temperature": 22.0,
            "feels_like": 24.0,
            "humidity": 70.0,
            "wind_speed": 8.0,
            "weather_condition": "clouds",
            "time_of_day": "afternoon",
            "season": "spring",
            "occasion": "casual"
        }
        response = requests.post(
            f"{BASE_URL}/recommend/women",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Women's recommendation successful!")
            print(f"   Top: {data.get('top')}")
            print(f"   Bottom: {data.get('bottom')}")
            print(f"   Outer: {data.get('outer')}")
            return data
        else:
            print(f"❌ Recommendation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Recommendation error: {e}")
        return None

def test_images(gender="men", label="shirt"):
    """Test images endpoint"""
    print(f"\n🔍 Testing /images endpoint (gender={gender}, label={label})...")
    try:
        response = requests.get(
            f"{BASE_URL}/images",
            params={"gender": gender, "label": label, "limit": 3}
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            items = data.get("items", [])
            print(f"✅ Images endpoint successful! Found {count} images")
            if items:
                print(f"   Sample URLs:")
                for i, url in enumerate(items[:3], 1):
                    print(f"   {i}. {BASE_URL}{url}")
            return data
        else:
            print(f"❌ Images endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Images error: {e}")
        return None

def main():
    print("=" * 50)
    print("🧪 WearSmart API Test Suite")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed. Please check your server and try again.")
        return
    
    # Test recommendations
    men_rec = test_men_recommendation()
    women_rec = test_women_recommendation()
    
    # Test images
    if men_rec:
        test_images("men", men_rec.get("top", "shirt"))
    
    if women_rec:
        test_images("women", women_rec.get("top", "shirts"))
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)
    print("\n💡 Tips:")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Health Check: http://localhost:8000/health")
    print("   - For mobile: Use your IP address instead of localhost")

if __name__ == "__main__":
    main()

