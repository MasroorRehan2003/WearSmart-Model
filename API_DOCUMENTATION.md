# WearSmart API Documentation for Mobile Integration

## 📋 Table of Contents
1. [Overview](#overview)
2. [Setup & Installation](#setup--installation)
3. [Running the FastAPI Server](#running-the-fastapi-server)
4. [API Endpoints](#api-endpoints)
5. [Request/Response Examples](#requestresponse-examples)
6. [Mobile Integration Guide](#mobile-integration-guide)
7. [Error Handling](#error-handling)
8. [Deployment](#deployment)

---

## Overview

The WearSmart API is a RESTful service that provides weather-based outfit recommendations for men and women. It uses machine learning models to predict appropriate clothing items (top, bottom, outerwear) based on weather conditions and user preferences.

### Key Features
- ✅ Weather-based outfit recommendations
- ✅ Separate models for Men and Women
- ✅ Image serving via static file endpoints
- ✅ CORS enabled for mobile app access
- ✅ Health check endpoint for monitoring

---

## Setup & Installation

### Prerequisites
- Python 3.8 or higher
- Model files: `weather_clothing_recommender.pkl` (Men) and `weather_clothing_recommender_women.pkl` (Women)
- Image folders: `clothing_images_men/` and `clothing_images/`

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install fastapi uvicorn joblib pandas pydantic python-multipart
```

### Step 2: Verify Required Files

Ensure these files/folders exist in your project directory:
```
weather_module/
├── unified_wearsmart.py
├── weather_clothing_recommender.pkl          # Men's model
├── weather_clothing_recommender_women.pkl    # Women's model
├── clothing_images_men/                      # Men's clothing images
│   ├── shirt/
│   ├── pants/
│   ├── jacket/
│   └── ...
└── clothing_images/                          # Women's clothing images
    ├── shirts/
    ├── jeans/
    ├── coat/
    └── ...
```

---

## Running the FastAPI Server

### Local Development

**Option 1: Using uvicorn command (Recommended)**
```bash
uvicorn unified_wearsmart:app --reload --port 8000
```

**Option 2: Using Python**
```python
import uvicorn
uvicorn.run("unified_wearsmart:app", host="0.0.0.0", port=8000, reload=True)
```

**Option 3: Production mode (no reload)**
```bash
uvicorn unified_wearsmart:app --host 0.0.0.0 --port 8000
```

### Server URLs
- **Local**: `http://localhost:8000`
- **Network**: `http://YOUR_IP_ADDRESS:8000` (for mobile testing)
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

### Finding Your IP Address (for mobile testing)

**Windows:**
```powershell
ipconfig
# Look for IPv4 Address under your active network adapter
```

**Mac/Linux:**
```bash
ifconfig
# or
ip addr show
```

---

## API Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running and models are loaded.

**Response:**
```json
{
  "status": "ok",
  "men_model_loaded": true,
  "women_model_loaded": true,
  "men_static": true,
  "women_static": true
}
```

**cURL Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Get Men's Outfit Recommendation

**POST** `/recommend/men`

Get outfit recommendations for men based on weather and preferences.

**Request Body:**
```json
{
  "temperature": 25.5,
  "feels_like": 27.0,
  "humidity": 65.0,
  "wind_speed": 10.5,
  "weather_condition": "clear",
  "time_of_day": "morning",
  "season": "summer",
  "mood": "Neutral",
  "occasion": "casual"
}
```

**Field Descriptions:**
- `temperature` (float): Current temperature in Celsius
- `feels_like` (float): Feels-like temperature in Celsius
- `humidity` (float): Humidity percentage (0-100)
- `wind_speed` (float): Wind speed in m/s
- `weather_condition` (string): Weather condition (e.g., "clear", "clouds", "rain", "snow")
- `time_of_day` (string): One of: "morning", "afternoon", "evening", "night"
- `season` (string): One of: "summer", "winter", "spring", "autumn", "fall"
- `mood` (string, optional): User mood (default: "Neutral")
- `occasion` (string): Occasion type (e.g., "casual", "formal", "party", "sports")

**Response:**
```json
{
  "top": "shirt",
  "bottom": "pants",
  "outer": "none"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/recommend/men" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 25.5,
    "feels_like": 27.0,
    "humidity": 65.0,
    "wind_speed": 10.5,
    "weather_condition": "clear",
    "time_of_day": "morning",
    "season": "summer",
    "mood": "Neutral",
    "occasion": "casual"
  }'
```

---

### 3. Get Women's Outfit Recommendation

**POST** `/recommend/women`

Get outfit recommendations for women based on weather and preferences.

**Request Body:**
```json
{
  "temperature": 22.0,
  "feels_like": 24.0,
  "humidity": 70.0,
  "wind_speed": 8.0,
  "weather_condition": "clouds",
  "time_of_day": "afternoon",
  "season": "spring",
  "occasion": "casual"
}
```

**Note:** Women's endpoint doesn't require `mood` field.

**Response:**
```json
{
  "top": "shirts",
  "bottom": "jeans",
  "outer": "jacket"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/recommend/women" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 22.0,
    "feels_like": 24.0,
    "humidity": 70.0,
    "wind_speed": 8.0,
    "weather_condition": "clouds",
    "time_of_day": "afternoon",
    "season": "spring",
    "occasion": "casual"
  }'
```

---

### 4. Get Images for Clothing Item

**GET** `/images`

Retrieve image URLs for a specific clothing item label.

**Query Parameters:**
- `gender` (required): "men" or "women"
- `label` (required): Clothing item label (e.g., "shirt", "pants", "jacket")
- `limit` (optional): Number of images to return (1-100, default: 10)

**Response:**
```json
{
  "count": 5,
  "items": [
    "/static/men/shirt/s1.jpg",
    "/static/men/shirt/s2.jpg",
    "/static/men/shirt/s3.jpg",
    "/static/men/shirt/s4.jpg",
    "/static/men/shirt/s5.jpg"
  ]
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/images?gender=men&label=shirt&limit=5"
```

**Full URL Example:**
If your server is running at `http://192.168.1.100:8000`, the full image URL would be:
```
http://192.168.1.100:8000/static/men/shirt/s1.jpg
```

---

## Request/Response Examples

### Complete Workflow Example

1. **Check API Health:**
```bash
GET http://localhost:8000/health
```

2. **Get Recommendation:**
```bash
POST http://localhost:8000/recommend/men
Body: {
  "temperature": 20.0,
  "feels_like": 18.0,
  "humidity": 80.0,
  "wind_speed": 15.0,
  "weather_condition": "rain",
  "time_of_day": "evening",
  "season": "winter",
  "mood": "Neutral",
  "occasion": "casual"
}
```

3. **Get Images for Recommended Items:**
```bash
GET http://localhost:8000/images?gender=men&label=jacket&limit=3
GET http://localhost:8000/images?gender=men&label=pants&limit=3
GET http://localhost:8000/images?gender=men&label=shirt&limit=3
```

---

## Mobile Integration Guide

### For React Native / Expo

```javascript
const API_BASE_URL = 'http://YOUR_IP_ADDRESS:8000';

// Get recommendation
const getRecommendation = async (gender, weatherData) => {
  try {
    const endpoint = gender === 'men' ? '/recommend/men' : '/recommend/women';
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(weatherData),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting recommendation:', error);
    throw error;
  }
};

// Get images for a clothing item
const getImages = async (gender, label, limit = 10) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/images?gender=${gender}&label=${label}&limit=${limit}`
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    // Convert relative URLs to absolute URLs
    const fullUrls = data.items.map(item => `${API_BASE_URL}${item}`);
    return fullUrls;
  } catch (error) {
    console.error('Error getting images:', error);
    throw error;
  }
};

// Example usage
const fetchOutfit = async () => {
  const weatherData = {
    temperature: 25.0,
    feels_like: 27.0,
    humidity: 65.0,
    wind_speed: 10.0,
    weather_condition: 'clear',
    time_of_day: 'morning',
    season: 'summer',
    occasion: 'casual',
  };
  
  // Get recommendation
  const recommendation = await getRecommendation('men', weatherData);
  console.log('Recommended:', recommendation);
  
  // Get images for each item
  const topImages = await getImages('men', recommendation.top);
  const bottomImages = await getImages('men', recommendation.bottom);
  const outerImages = recommendation.outer !== 'none' 
    ? await getImages('men', recommendation.outer)
    : [];
  
  return {
    recommendation,
    images: {
      top: topImages,
      bottom: bottomImages,
      outer: outerImages,
    },
  };
};
```

### For Flutter / Dart

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class WearSmartAPI {
  static const String baseUrl = 'http://YOUR_IP_ADDRESS:8000';
  
  // Get recommendation
  static Future<Map<String, dynamic>> getRecommendation(
    String gender,
    Map<String, dynamic> weatherData,
  ) async {
    final endpoint = gender == 'men' ? '/recommend/men' : '/recommend/women';
    final url = Uri.parse('$baseUrl$endpoint');
    
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(weatherData),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get recommendation: ${response.statusCode}');
    }
  }
  
  // Get images
  static Future<List<String>> getImages(
    String gender,
    String label, {
    int limit = 10,
  }) async {
    final url = Uri.parse(
      '$baseUrl/images?gender=$gender&label=$label&limit=$limit',
    );
    
    final response = await http.get(url);
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final items = List<String>.from(data['items']);
      // Convert to full URLs
      return items.map((item) => '$baseUrl$item').toList();
    } else {
      throw Exception('Failed to get images: ${response.statusCode}');
    }
  }
  
  // Health check
  static Future<Map<String, dynamic>> checkHealth() async {
    final url = Uri.parse('$baseUrl/health');
    final response = await http.get(url);
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Health check failed: ${response.statusCode}');
    }
  }
}

// Example usage
Future<void> fetchOutfit() async {
  final weatherData = {
    'temperature': 25.0,
    'feels_like': 27.0,
    'humidity': 65.0,
    'wind_speed': 10.0,
    'weather_condition': 'clear',
    'time_of_day': 'morning',
    'season': 'summer',
    'occasion': 'casual',
  };
  
  try {
    // Get recommendation
    final recommendation = await WearSmartAPI.getRecommendation('men', weatherData);
    print('Recommended: $recommendation');
    
    // Get images
    final topImages = await WearSmartAPI.getImages('men', recommendation['top']);
    final bottomImages = await WearSmartAPI.getImages('men', recommendation['bottom']);
    final outerImages = recommendation['outer'] != 'none'
        ? await WearSmartAPI.getImages('men', recommendation['outer'])
        : <String>[];
    
    print('Top images: $topImages');
    print('Bottom images: $bottomImages');
    print('Outer images: $outerImages');
  } catch (e) {
    print('Error: $e');
  }
}
```

### For Android (Java/Kotlin)

```kotlin
// Using Retrofit or OkHttp
data class RecommendationRequest(
    val temperature: Double,
    val feels_like: Double,
    val humidity: Double,
    val wind_speed: Double,
    val weather_condition: String,
    val time_of_day: String,
    val season: String,
    val occasion: String,
    val mood: String = "Neutral"
)

data class RecommendationResponse(
    val top: String,
    val bottom: String,
    val outer: String
)

// Retrofit Interface
interface WearSmartAPI {
    @POST("/recommend/men")
    suspend fun getMenRecommendation(
        @Body request: RecommendationRequest
    ): RecommendationResponse
    
    @POST("/recommend/women")
    suspend fun getWomenRecommendation(
        @Body request: RecommendationRequest
    ): RecommendationResponse
    
    @GET("/images")
    suspend fun getImages(
        @Query("gender") gender: String,
        @Query("label") label: String,
        @Query("limit") limit: Int = 10
    ): ImageResponse
    
    @GET("/health")
    suspend fun checkHealth(): HealthResponse
}
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid time_of_day. Must be one of: morning, afternoon, evening, night"
}
```

**404 Not Found:**
```json
{
  "detail": "Images root not found: clothing_images_men"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Men model not loaded"
}
```
or
```json
{
  "detail": "Prediction failed: [error message]"
}
```

### Handling Errors in Mobile Apps

```javascript
try {
  const response = await fetch(`${API_BASE_URL}/recommend/men`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(weatherData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }
  
  const data = await response.json();
  return data;
} catch (error) {
  console.error('API Error:', error.message);
  // Show user-friendly error message
  alert(`Failed to get recommendation: ${error.message}`);
}
```

---

## Deployment

### Local Network Access (for Development)

1. Find your computer's IP address
2. Run server with `--host 0.0.0.0`:
   ```bash
   uvicorn unified_wearsmart:app --host 0.0.0.0 --port 8000
   ```
3. Update mobile app to use: `http://YOUR_IP:8000`

### Production Deployment Options

**1. Render.com:**
- Create new Web Service
- Connect GitHub repository
- Set build command: `pip install -r requirements.txt`
- Set start command: `uvicorn unified_wearsmart:app --host 0.0.0.0 --port $PORT`
- Add environment variables if needed

**2. Railway:**
- Connect repository
- Railway auto-detects FastAPI
- Ensure `requirements.txt` is present
- Deploy automatically

**3. Azure App Service:**
- Create Python web app
- Deploy via Git or ZIP
- Configure startup command: `uvicorn unified_wearsmart:app --host 0.0.0.0 --port 8000`

**4. Docker (Optional):**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "unified_wearsmart:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Important Notes

1. **CORS**: The API has CORS enabled for all origins (`*`). For production, restrict this to your mobile app's domain.

2. **Image URLs**: Image URLs returned are relative paths. You need to prepend your server URL to get full URLs.

3. **Model Files**: Ensure `.pkl` model files are included in deployment.

4. **Image Folders**: Ensure image folders are included in deployment or use cloud storage.

5. **Weather Data**: Your mobile app needs to fetch weather data from a weather API (e.g., OpenWeatherMap) and pass it to the recommendation endpoints.

---

## Support

For issues or questions:
1. Check the `/health` endpoint to verify models are loaded
2. Check server logs for error messages
3. Verify all required files and folders exist
4. Test endpoints using the Swagger UI at `/docs`

---

**Last Updated:** 2024

