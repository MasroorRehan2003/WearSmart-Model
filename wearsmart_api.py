# ML MODELS DISABLED — using RULE-BASED recommendation
"""
WearSmart API — FastAPI Backend Only

This file is CLEANED. No BLIP. No Gradio. No UI.
Perfect for React Native, FlutterFlow, Expo, Kotlin, etc.

Run: uvicorn wearsmart_api:app --reload --port 8000
"""

import os
import random
from glob import glob
from typing import List, Optional

# import joblib  # COMMENTED OUT - not needed for rule-based system
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# MongoDB imports
try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("⚠️ pymongo not installed. /cloud-images endpoint will not work.")

# ===========================================
# CONFIG
# ===========================================

# MEN_MODEL_PATH = "weather_clothing_recommender.pkl"  # COMMENTED OUT
# WOMEN_MODEL_PATH = "weather_clothing_recommender_women.pkl"  # COMMENTED OUT
MEN_IMAGES_ROOT = "clothing_images_men"
WOMEN_IMAGES_ROOT = "clothing_images"
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# MongoDB Configuration
# Try environment variable first (Railway), then fallback to default
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://i211707_db_user:2103921@cluster0.124kx3o.mongodb.net/wearsmart?retryWrites=true&w=majority"
)

# Log MongoDB URI status (without exposing password)
if MONGODB_URI:
    uri_parts = MONGODB_URI.split("@")
    if len(uri_parts) > 1:
        safe_uri = f"mongodb+srv://***@{uri_parts[1]}"
        print(f"📦 MongoDB URI configured: {safe_uri}")
    else:
        print("📦 MongoDB URI configured")
else:
    print("⚠️ MongoDB URI not found - set MONGODB_URI environment variable")

DATABASE_NAME = "wearsmart"
COLLECTION_NAME = "clothing_images"

# MongoDB connection (lazy initialization)
_mongodb_client: Optional[MongoClient] = None
_mongodb_db = None
_mongodb_collection = None

def get_mongodb_collection():
    """Get MongoDB collection (lazy initialization)"""
    global _mongodb_client, _mongodb_db, _mongodb_collection
    
    if not MONGODB_AVAILABLE:
        print("⚠️ pymongo not available")
        return None
    
    if not MONGODB_URI or MONGODB_URI == "YOUR_MONGODB_CONNECTION_STRING_HERE":
        print("⚠️ MongoDB URI not configured")
        return None
    
    if _mongodb_collection is not None:
        return _mongodb_collection
    
    try:
        print(f"🔌 Attempting MongoDB connection...")
        _mongodb_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        _mongodb_db = _mongodb_client[DATABASE_NAME]
        _mongodb_collection = _mongodb_db[COLLECTION_NAME]
        
        # Test connection with timeout
        _mongodb_client.admin.command('ping')
        print(f"✅ MongoDB connected successfully to database: {DATABASE_NAME}")
        return _mongodb_collection
    except Exception as e:
        error_msg = str(e)
        print(f"❌ MongoDB connection error: {error_msg}")
        
        # More specific error messages
        if "authentication" in error_msg.lower() or "password" in error_msg.lower():
            print("   💡 Check your MongoDB username and password")
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            print("   💡 Check your IP whitelist in MongoDB Atlas")
        elif "could not be resolved" in error_msg.lower():
            print("   💡 Check your MongoDB connection string format")
        
        return None

# ===========================================
# FASTAPI APP
# ===========================================

app = FastAPI(title="WearSmart Mobile API", version="2.0")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)

# -------------------------------------------
# Load models ONCE (with error handling) - COMMENTED OUT
# -------------------------------------------

# _men_model, _women_model = None, None
# _men_model_error, _women_model_error = None, None

# def load_model_safely(model_path: str, model_name: str):
#     """Load model with error handling for version compatibility"""
#     if not os.path.exists(model_path):
#         print(f"⚠️ {model_name} model file not found: {model_path}")
#         return None, f"Model file not found: {model_path}"
#     
#     try:
#         model = joblib.load(model_path)
#         print(f"✅ {model_name} model loaded successfully")
#         return model, None
#     except KeyError as e:
#         error_msg = f"Model compatibility error (KeyError {e}). This usually means the model was saved with a different scikit-learn version."
#         print(f"❌ {error_msg}")
#         return None, error_msg
#     except Exception as e:
#         error_msg = f"Failed to load {model_name} model: {str(e)}"
#         print(f"❌ {error_msg}")
#         return None, error_msg

# Load models
# _men_model, _men_model_error = load_model_safely(MEN_MODEL_PATH, "Men's")
# _women_model, _women_model_error = load_model_safely(WOMEN_MODEL_PATH, "Women's")

print("✅ Using RULE-BASED recommendation system (ML models disabled)")

# -------------------------------------------
# Mount image folders
# -------------------------------------------

if os.path.isdir(MEN_IMAGES_ROOT):
    app.mount("/static/men", StaticFiles(directory=MEN_IMAGES_ROOT), name="men_static")

if os.path.isdir(WOMEN_IMAGES_ROOT):
    app.mount("/static/women", StaticFiles(directory=WOMEN_IMAGES_ROOT), name="women_static")

# ===========================================
# REQUEST / RESPONSE MODELS
# ===========================================

class MenRequest(BaseModel):
    temperature: float
    feels_like: float
    humidity: float
    wind_speed: float
    weather_condition: str
    time_of_day: str = Field(pattern=r"^(morning|afternoon|evening|night)$")
    season: str = Field(pattern=r"^(summer|winter|spring|autumn|fall)$")
    mood: str = "Neutral"
    occasion: str

class WomenRequest(BaseModel):
    temperature: float
    feels_like: float
    humidity: float
    wind_speed: float
    weather_condition: str
    time_of_day: str = Field(pattern=r"^(morning|afternoon|evening|night)$")
    season: str = Field(pattern=r"^(summer|winter|spring|autumn|fall)$")
    occasion: str

class OutfitResponse(BaseModel):
    top: str
    bottom: str
    outer: str

# ===========================================
# RULE-BASED RECOMMENDATION ENGINE
# ===========================================

def rule_based_recommender(gender: str, data: dict) -> tuple:
    """
    Rule-based clothing recommendation system.
    Uses only actual clothing categories from image folders.
    
    MEN'S CATEGORIES:
    - Tops: T-Shirt, Shirt, Sweater, Hoodie, Kurta
    - Bottoms: Jeans, Pants, Shorts
    - Outer: Jacket, Coat, None
    
    WOMEN'S CATEGORIES:
    - Tops: Tops, Kurtas
    - Bottoms: Jeans, Capris, Trousers, Leggings, Dupatta
    - Outer: Jacket, Coat, Puffer_Jacket, None
    
    Args:
        gender: "men" or "women"
        data: dict with keys: temperature, feels_like, weather_condition, 
              season, time_of_day, occasion, mood (for men only)
    
    Returns:
        tuple: (top, bottom, outer)
    """
    temp = data.get("temperature", 20)
    feels_like = data.get("feels_like", temp)
    weather = data.get("weather_condition", "").lower()
    season = data.get("season", "").lower()
    occasion = data.get("occasion", "").lower()
    time_of_day = data.get("time_of_day", "").lower()
    mood = data.get("mood", "neutral").lower() if gender == "men" else "neutral"
    wind_speed = data.get("wind_speed", 0)
    
    # Normalize season names
    if season == "fall":
        season = "autumn"
    
    # Initialize defaults based on gender
    if gender == "men":
        top = "Shirt"
        bottom = "Jeans"
        outer = "None"
    else:
        top = "Tops"
        bottom = "Jeans"
        outer = "None"
    
    # ===================================
    # TEMPERATURE-BASED LOGIC
    # ===================================
    
    if temp >= 30:  # Very Hot (30°C+)
        if gender == "men":
            top = "T-Shirt"
            bottom = "Shorts"
            outer = "None"
        else:
            top = "Tops"
            bottom = "Capris"
            outer = "None"
    
    elif 25 <= temp < 30:  # Hot (25-29°C)
        if gender == "men":
            top = "T-Shirt"
            bottom = "Pants" if occasion in ["work", "formal", "business"] else "Shorts"
            outer = "None"
        else:
            top = "Tops"
            bottom = "Capris" if occasion == "casual" else "Trousers"
            outer = "None"
    
    elif 20 <= temp < 25:  # Warm (20-24°C)
        if gender == "men":
            top = "Shirt"
            bottom = "Jeans" if occasion == "casual" else "Pants"
            outer = "None"
        else:
            top = "Tops"
            bottom = "Jeans"
            outer = "Jacket" if feels_like < 22 else "None"
    
    elif 15 <= temp < 20:  # Mild (15-19°C)
        if gender == "men":
            top = "Shirt"
            bottom = "Jeans"
            outer = "Jacket" if feels_like < 17 else "None"
        else:
            top = "Tops"
            bottom = "Jeans"
            outer = "Coat" if feels_like < 17 else "Jacket"
    
    elif 10 <= temp < 15:  # Cool (10-14°C)
        if gender == "men":
            top = "Sweater"
            bottom = "Jeans"
            outer = "Jacket"
        else:
            top = "Tops"
            bottom = "Jeans"
            outer = "Coat"
    
    elif 5 <= temp < 10:  # Cold (5-9°C)
        if gender == "men":
            top = "Hoodie"
            bottom = "Jeans"
            outer = "Jacket"
        else:
            top = "Tops"
            bottom = "Leggings"
            outer = "Coat"
    
    else:  # Very Cold (<5°C)
        if gender == "men":
            top = "Sweater"
            bottom = "Pants"
            outer = "Coat"
        else:
            top = "Tops"
            bottom = "Leggings"
            outer = "Puffer_Jacket"
    
    # ===================================
    # WEATHER CONDITION OVERRIDES
    # ===================================
    
    if "rain" in weather or "drizzle" in weather:
        if gender == "men":
            outer = "Jacket"
        else:
            outer = "Coat"
    
    elif "snow" in weather or "blizzard" in weather:
        if gender == "men":
            top = "Sweater"
            bottom = "Pants"
            outer = "Coat"
        else:
            top = "Tops"
            bottom = "Leggings"
            outer = "Puffer_Jacket"
    
    elif "storm" in weather or "thunder" in weather:
        outer = "Coat"
    
    elif "wind" in weather or wind_speed > 20:
        if outer == "None":
            if gender == "men":
                outer = "Jacket"
            else:
                outer = "Coat"
    
    # ===================================
    # OCCASION-BASED REFINEMENTS
    # ===================================
    
    if "formal" in occasion or "wedding" in occasion or "business" in occasion or "office" in occasion:
        if gender == "men":
            top = "Shirt"
            bottom = "Pants"
            outer = "Coat" if temp < 15 else "Jacket" if temp < 20 else "None"
        else:
            top = "Tops"
            bottom = "Trousers"
            outer = "Coat" if temp < 15 else "Jacket" if temp < 20 else "None"
    
    elif "party" in occasion or "night out" in occasion or "club" in occasion:
        if gender == "men":
            top = "Shirt"
            bottom = "Jeans"
            outer = "Jacket" if temp < 20 else "None"
        else:
            top = "Tops"
            bottom = "Jeans"
            outer = "Jacket" if temp < 18 else "None"
    
    elif "gym" in occasion or "workout" in occasion or "sports" in occasion or "exercise" in occasion:
        if gender == "men":
            top = "T-Shirt"
            bottom = "Shorts"
            outer = "Hoodie" if temp < 15 else "None"
        else:
            top = "Tops"
            bottom = "Leggings"
            outer = "Jacket" if temp < 15 else "None"
    
    elif "casual" in occasion or "daily" in occasion or "everyday" in occasion:
        if gender == "men":
            top = "T-Shirt" if temp > 20 else "Hoodie"
            bottom = "Jeans"
            outer = "None" if temp > 20 else "Jacket"
        else:
            top = "Tops"
            bottom = "Jeans"
            outer = "None" if temp > 20 else "Jacket"
    
    elif "traditional" in occasion or "ethnic" in occasion or "cultural" in occasion:
        if gender == "men":
            top = "Kurta"
            bottom = "Pants"
            outer = "Jacket" if temp < 15 else "None"
        else:
            top = "Kurtas"
            bottom = "Dupatta"
            outer = "None"
    
    elif "date" in occasion or "romantic" in occasion:
        if gender == "men":
            top = "Shirt"
            bottom = "Jeans"
            outer = "Jacket" if temp < 20 else "None"
        else:
            top = "Tops"
            bottom = "Jeans"
            outer = "Jacket" if temp < 18 else "None"
    
    # ===================================
    # TIME OF DAY REFINEMENTS
    # ===================================
    
    if time_of_day == "evening" or time_of_day == "night":
        # Evening/night typically gets cooler
        if temp < 18 and outer == "None":
            outer = "Jacket"
        
        # For very cold evenings
        if temp < 12 and outer == "Jacket":
            outer = "Coat"
    
    elif time_of_day == "morning":
        # Mornings can be cooler than afternoon
        if temp < 15 and outer == "None":
            outer = "Jacket"
    
    # ===================================
    # MOOD-BASED REFINEMENTS (MEN ONLY)
    # ===================================
    
    if gender == "men":
        if "confident" in mood or "bold" in mood or "energetic" in mood:
            if temp < 20 and outer == "None":
                outer = "Jacket"
        
        elif "relaxed" in mood or "comfortable" in mood or "chill" in mood:
            if occasion == "casual":
                top = "Hoodie"
                bottom = "Jeans"
                if temp < 15:
                    outer = "Jacket"
        
        elif "professional" in mood or "focused" in mood:
            if top == "T-Shirt":
                top = "Shirt"
    
    # ===================================
    # SEASON-BASED ADJUSTMENTS
    # ===================================
    
    if season == "winter":
        if outer == "None" and temp < 15:
            outer = "Jacket" if temp > 10 else "Coat"
        
        # Extra cold winter days
        if temp < 5:
            if gender == "men":
                outer = "Coat"
                top = "Sweater"
            else:
                outer = "Puffer_Jacket"
    
    elif season == "summer":
        if temp > 25 and outer in ["Jacket", "Coat"]:
            outer = "None"
    
    elif season == "autumn" or season == "spring":
        # Transitional seasons - layer up slightly
        if temp < 20 and outer == "None":
            outer = "Jacket"
    
    # ===================================
    # HUMIDITY ADJUSTMENTS
    # ===================================
    
    humidity = data.get("humidity", 50)
    if humidity > 80:
        # High humidity feels warmer - lighter clothing
        if gender == "men":
            if temp > 25 and top == "Shirt":
                top = "T-Shirt"
        else:
            if temp > 25 and outer == "Jacket":
                outer = "None"
    
    # ===================================
    # FINAL VALIDATION
    # Ensure all values match actual folder names
    # ===================================
    
    if gender == "men":
        # Validate men's categories
        valid_tops = ["T-Shirt", "Shirt", "Sweater", "Hoodie", "Kurta"]
        valid_bottoms = ["Jeans", "Pants", "Shorts"]
        valid_outer = ["Jacket", "Coat", "None"]
        
        if top not in valid_tops:
            top = "Shirt"
        if bottom not in valid_bottoms:
            bottom = "Jeans"
        if outer not in valid_outer:
            outer = "None"
    else:
        # Validate women's categories
        valid_tops = ["Tops", "Kurtas"]
        valid_bottoms = ["Jeans", "Capris", "Trousers", "Leggings", "Dupatta"]
        valid_outer = ["Jacket", "Coat", "Puffer_Jacket", "None"]
        
        if top not in valid_tops:
            top = "Tops"
        if bottom not in valid_bottoms:
            bottom = "Jeans"
        if outer not in valid_outer:
            outer = "None"
    
    return (top, bottom, outer)

# ===========================================
# UTIL
# ===========================================

def pick_images(root: str, label: str, limit=10) -> List[str]:
    """
    Pick random images from a category folder.
    
    Args:
        root: Root directory (MEN_IMAGES_ROOT or WOMEN_IMAGES_ROOT)
        label: Clothing category label
        limit: Maximum number of images to return
    
    Returns:
        List of image file paths
    """
    folder = os.path.join(root, label.lower())
    if not os.path.isdir(folder):
        return []
    
    files = [
        f for f in glob(folder + "/*")
        if os.path.splitext(f)[1].lower() in VALID_EXTS
    ]
    random.shuffle(files)
    return files[:limit]

# ===========================================
# ENDPOINTS
# ===========================================

@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "WearSmart API - Rule-Based Clothing Recommendation System",
        "version": "2.0",
        "endpoints": {
            "health": "/health",
            "men_recommend": "/recommend/men",
            "women_recommend": "/recommend/women",
            "images": "/images?gender=men&label=shirt&limit=10",
            "cloud_images": "/cloud-images?gender=men&label=shirt&limit=10"
        },
        "documentation": "/docs"
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "recommendation_system": "rule-based",
        # "men_model_loaded": _men_model is not None,  # COMMENTED OUT
        # "women_model_loaded": _women_model is not None,  # COMMENTED OUT
        # "men_model_error": _men_model_error,  # COMMENTED OUT
        # "women_model_error": _women_model_error,  # COMMENTED OUT
        "men_images_available": os.path.isdir(MEN_IMAGES_ROOT),
        "women_images_available": os.path.isdir(WOMEN_IMAGES_ROOT),
        "mongodb_configured": MONGODB_URI is not None and MONGODB_URI != "",
    }

# -------------------------------------------
# MEN RECOMMENDER
# -------------------------------------------

@app.post("/recommend/men", response_model=OutfitResponse)
def recommend_men(req: MenRequest):
    """
    Get clothing recommendation for men based on weather and preferences.
    
    Args:
        req: MenRequest with weather data and preferences
    
    Returns:
        OutfitResponse with top, bottom, and outer clothing recommendations
    """
    # COMMENTED OUT - ML MODEL PREDICTION
    # if _men_model is None:
    #     error_detail = _men_model_error or "Men model not loaded"
    #     raise HTTPException(
    #         status_code=503,
    #         detail=f"Men model not available. {error_detail}"
    #     )
    # 
    # df = pd.DataFrame([req.dict()])
    # top, bottom, outer = _men_model.predict(df)[0]
    
    # NEW - RULE-BASED PREDICTION
    top, bottom, outer = rule_based_recommender("men", req.dict())
    
    return OutfitResponse(
        top=str(top),
        bottom=str(bottom),
        outer=str(outer)
    )

# -------------------------------------------
# WOMEN RECOMMENDER
# -------------------------------------------

@app.post("/recommend/women", response_model=OutfitResponse)
def recommend_women(req: WomenRequest):
    """
    Get clothing recommendation for women based on weather and preferences.
    
    Args:
        req: WomenRequest with weather data and preferences
    
    Returns:
        OutfitResponse with top, bottom, and outer clothing recommendations
    """
    # COMMENTED OUT - ML MODEL PREDICTION
    # if _women_model is None:
    #     error_detail = _women_model_error or "Women model not loaded"
    #     raise HTTPException(
    #         status_code=503,
    #         detail=f"Women model not available. {error_detail}"
    #     )
    # 
    # df = pd.DataFrame([req.dict()])
    # top, bottom, outer = _women_model.predict(df)[0]
    
    # NEW - RULE-BASED PREDICTION
    top, bottom, outer = rule_based_recommender("women", req.dict())
    
    return OutfitResponse(
        top=str(top),
        bottom=str(bottom),
        outer=str(outer)
    )

# -------------------------------------------
# IMAGES (MEN + WOMEN)
# -------------------------------------------

@app.get("/images")
def get_images(
    gender: str = Query(..., pattern="^(men|women)$"),
    label: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get local image URLs for a clothing category.
    
    Args:
        gender: "men" or "women"
        label: Clothing category (e.g., "shirt", "jeans", "jacket")
        limit: Maximum number of images to return (1-50)
    
    Returns:
        JSON with count and list of image URLs
    """
    root = MEN_IMAGES_ROOT if gender == "men" else WOMEN_IMAGES_ROOT
    paths = pick_images(root, label, limit)
    
    base_url = f"/static/{gender}"
    urls = [
        f"{base_url}/{label.lower()}/{os.path.basename(p)}"
        for p in paths
    ]
    
    return {"count": len(urls), "items": urls}

# -------------------------------------------
# CLOUD IMAGES (MongoDB + Cloudinary)
# -------------------------------------------

@app.get("/cloud-images")
def get_cloud_images(
    gender: str = Query(..., pattern="^(men|women)$"),
    label: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get Cloudinary image URLs from MongoDB.
    Returns images stored in MongoDB with Cloudinary URLs.
    
    Args:
        gender: "men" or "women"
        label: Clothing category (e.g., "shirt", "jeans", "jacket")
        limit: Maximum number of images to return (1-50)
    
    Returns:
        JSON with count and list of image data including Cloudinary URLs
    """
    if not MONGODB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="MongoDB not available. Install pymongo: pip install pymongo"
        )
    
    collection = get_mongodb_collection()
    if collection is None:
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to MongoDB. Check connection string and ensure IP is whitelisted."
        )
    
    try:
        # Query MongoDB for images matching gender and label
        query = {
            "gender": gender,
            "label": label.lower()
        }
        
        # Find documents with Cloudinary URLs
        docs = list(collection.find(query).limit(limit))
        
        if not docs:
            return {
                "count": 0,
                "items": [],
                "message": f"No images found for gender='{gender}', label='{label}'"
            }
        
        # Format response
        images = []
        for doc in docs:
            cloudinary_url = doc.get("cloudinary_url", "")
            if cloudinary_url:  # Only include if Cloudinary URL exists
                images.append({
                    "filename": doc.get("filename", ""),
                    "label": doc.get("label", ""),
                    "url": cloudinary_url,
                    "public_id": doc.get("cloudinary_public_id", ""),
                    "width": doc.get("image_width", 0),
                    "height": doc.get("image_height", 0),
                    "file_size": doc.get("file_size", 0),
                    "uploaded_at": str(doc.get("uploaded_at", ""))
                })
        
        return {
            "count": len(images),
            "items": images
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying MongoDB: {str(e)}"
        )