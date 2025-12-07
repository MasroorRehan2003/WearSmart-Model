"""
WearSmart API — FastAPI Backend Only
This file is CLEANED. No BLIP. No Gradio. No UI.
Perfect for React Native, FlutterFlow, Expo, Kotlin, etc.

Run:
    uvicorn wearsmart_api:app --reload --port 8000
"""

import os
import random
from glob import glob
from typing import List, Optional

import joblib
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

MEN_MODEL_PATH = "weather_clothing_recommender.pkl"
WOMEN_MODEL_PATH = "weather_clothing_recommender_women.pkl"

MEN_IMAGES_ROOT = "clothing_images_men"
WOMEN_IMAGES_ROOT = "clothing_images"

VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# MongoDB Configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://i211707_db_user:2103921@cluster0.124kx3o.mongodb.net/wearsmart?retryWrites=true&w=majority"
)
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
        return None
    
    if _mongodb_collection is not None:
        return _mongodb_collection
    
    try:
        _mongodb_client = MongoClient(MONGODB_URI)
        _mongodb_db = _mongodb_client[DATABASE_NAME]
        _mongodb_collection = _mongodb_db[COLLECTION_NAME]
        # Test connection
        _mongodb_client.admin.command('ping')
        return _mongodb_collection
    except Exception as e:
        print(f"⚠️ MongoDB connection error: {e}")
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
# Load models ONCE (with error handling)
# -------------------------------------------

_men_model, _women_model = None, None
_men_model_error, _women_model_error = None, None

def load_model_safely(model_path: str, model_name: str):
    """Load model with error handling for version compatibility"""
    if not os.path.exists(model_path):
        print(f"⚠️ {model_name} model file not found: {model_path}")
        return None, f"Model file not found: {model_path}"
    
    try:
        model = joblib.load(model_path)
        print(f"✅ {model_name} model loaded successfully")
        return model, None
    except KeyError as e:
        error_msg = f"Model compatibility error (KeyError {e}). This usually means the model was saved with a different scikit-learn version."
        print(f"❌ {error_msg}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Failed to load {model_name} model: {str(e)}"
        print(f"❌ {error_msg}")
        return None, error_msg

# Load models
_men_model, _men_model_error = load_model_safely(MEN_MODEL_PATH, "Men's")
_women_model, _women_model_error = load_model_safely(WOMEN_MODEL_PATH, "Women's")

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
# UTIL
# ===========================================

def pick_images(root: str, label: str, limit=10) -> List[str]:
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

@app.get("/health")
def health():
    return {
        "status": "ok",
        "men_model_loaded": _men_model is not None,
        "women_model_loaded": _women_model is not None,
        "men_model_error": _men_model_error,
        "women_model_error": _women_model_error,
        "men_images_available": os.path.isdir(MEN_IMAGES_ROOT),
        "women_images_available": os.path.isdir(WOMEN_IMAGES_ROOT),
    }

# -------------------------------------------
# MEN RECOMMENDER
# -------------------------------------------

@app.post("/recommend/men", response_model=OutfitResponse)
def recommend_men(req: MenRequest):
    if _men_model is None:
        error_detail = _men_model_error or "Men model not loaded"
        raise HTTPException(
            status_code=503,
            detail=f"Men model not available. {error_detail}"
        )

    df = pd.DataFrame([req.dict()])
    top, bottom, outer = _men_model.predict(df)[0]

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
    if _women_model is None:
        error_detail = _women_model_error or "Women model not loaded"
        raise HTTPException(
            status_code=503,
            detail=f"Women model not available. {error_detail}"
        )

    df = pd.DataFrame([req.dict()])
    top, bottom, outer = _women_model.predict(df)[0]

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
    root = MEN_IMAGES_ROOT if gender == "men" else WOMEN_IMAGES_ROOT

    paths = pick_images(root, label, limit)

    base_url = f"/static/{gender}"

    urls = [
        f"{base_url}/{label}/{os.path.basename(p)}"
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
            detail="Failed to connect to MongoDB. Check connection string."
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
