# Quick Start Guide - WearSmart FastAPI

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Verify Files Exist
Make sure you have:
- ✅ `weather_clothing_recommender.pkl` (Men's model)
- ✅ `weather_clothing_recommender_women.pkl` (Women's model)
- ✅ `clothing_images_men/` folder with subfolders
- ✅ `clothing_images/` folder with subfolders

### Step 3: Run the Server
```bash
uvicorn unified_wearsmart:app --reload --port 8000
```

## 📱 For Mobile Testing

### Find Your IP Address

**Windows PowerShell:**
```powershell
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.1.100)
```

**Mac/Linux:**
```bash
ifconfig | grep "inet "
```

### Run Server for Network Access
```bash
uvicorn unified_wearsmart:app --host 0.0.0.0 --port 8000
```

### Update Mobile App
Use: `http://YOUR_IP_ADDRESS:8000` as your API base URL

## 🧪 Test the API

### 1. Health Check
Open in browser: `http://localhost:8000/health`

### 2. API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Test with cURL

**Get Men's Recommendation:**
```bash
curl -X POST "http://localhost:8000/recommend/men" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 25.0,
    "feels_like": 27.0,
    "humidity": 65.0,
    "wind_speed": 10.0,
    "weather_condition": "clear",
    "time_of_day": "morning",
    "season": "summer",
    "occasion": "casual"
  }'
```

**Get Images:**
```bash
curl "http://localhost:8000/images?gender=men&label=shirt&limit=5"
```

## 📋 Common Issues

**Problem:** Models not loading
- **Solution:** Check if `.pkl` files exist in the project directory

**Problem:** Images not found
- **Solution:** Verify image folders exist and contain subfolders with images

**Problem:** Mobile app can't connect
- **Solution:** 
  1. Use `--host 0.0.0.0` when running server
  2. Check firewall settings
  3. Ensure mobile device is on same network
  4. Use IP address, not `localhost`

**Problem:** CORS errors
- **Solution:** CORS is already enabled for all origins. If issues persist, check server logs.

## 📚 Full Documentation
See `API_DOCUMENTATION.md` for complete API reference and mobile integration examples.

