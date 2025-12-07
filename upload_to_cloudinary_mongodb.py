"""
Upload images to Cloudinary and store URLs in MongoDB Atlas
Uploads 1 image from each folder in clothing_images_men and clothing_images
"""

import os
import random
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

try:
    from cloudinary import uploader as cloudinary_uploader
    from cloudinary import utils as cloudinary_utils
    import cloudinary
except ImportError:
    print("❌ cloudinary not installed. Install it with: pip install cloudinary")
    exit(1)

try:
    from pymongo import MongoClient
except ImportError:
    print("❌ pymongo not installed. Install it with: pip install pymongo")
    exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
except ImportError:
    print("⚠️ python-dotenv not installed. Install it with: pip install python-dotenv")
    print("   Continuing without .env file support...")

# ===========================================
# CONFIGURATION
# ===========================================

# Cloudinary Configuration (from environment variables)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

# MongoDB Atlas Connection String
MONGODB_URI = os.getenv(
    "MONGODB_URI", 
    "mongodb+srv://i211707_db_user:2103921@cluster0.124kx3o.mongodb.net/wearsmart?retryWrites=true&w=majority"
)

# Database and Collection names
DATABASE_NAME = "wearsmart"
COLLECTION_NAME = "clothing_images"

# Local image directories
MEN_IMAGES_ROOT = "clothing_images_men"
WOMEN_IMAGES_ROOT = "clothing_images"

# Valid image extensions
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# ===========================================
# CLOUDINARY SETUP
# ===========================================

def setup_cloudinary():
    """Configure Cloudinary with credentials"""
    if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_API_KEY or not CLOUDINARY_API_SECRET:
        print("❌ Cloudinary credentials not found!")
        print("   Please set these environment variables in your .env file:")
        print("   - CLOUDINARY_CLOUD_NAME")
        print("   - CLOUDINARY_API_KEY")
        print("   - CLOUDINARY_API_SECRET")
        return False
    
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )
    
    print("✅ Cloudinary configured successfully!")
    return True

# ===========================================
# MONGODB CONNECTION
# ===========================================

def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    try:
        if MONGODB_URI == "YOUR_MONGODB_CONNECTION_STRING_HERE":
            print("❌ Please set your MongoDB connection string!")
            return None, None
        
        client = MongoClient(MONGODB_URI)
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        return client, collection
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Check your connection string")
        print("   - Ensure your IP is whitelisted in MongoDB Atlas")
        print("   - Check your username/password")
        return None, None

# ===========================================
# IMAGE PROCESSING
# ===========================================

def get_one_image_from_folder(folder_path: Path) -> Optional[Path]:
    """Get one random image from a folder"""
    if not folder_path.is_dir():
        return None
    
    # Get all image files
    image_files = [
        f for f in folder_path.iterdir()
        if f.is_file() and f.suffix.lower() in VALID_EXTS
    ]
    
    if not image_files:
        return None
    
    # Return one random image
    return random.choice(image_files)

def upload_image_to_cloudinary(
    image_path: Path,
    folder_name: str,
    gender: str
) -> Optional[dict]:
    """Upload image to Cloudinary and return result"""
    try:
        # Cloudinary folder path: wearsmart/gender/label
        cloudinary_folder = f"wearsmart/{gender}/{folder_name}"
        
        result = cloudinary_uploader.upload(
            str(image_path),
            folder=cloudinary_folder,
            use_filename=True,
            unique_filename=False,
            overwrite=False  # Don't overwrite if file exists
        )
        
        return result
    except Exception as e:
        print(f"   ❌ Cloudinary upload error: {e}")
        return None

def save_to_mongodb(
    collection,
    image_path: Path,
    label: str,
    gender: str,
    cloudinary_result: dict
):
    """Save image metadata and Cloudinary URL to MongoDB (upsert - update if exists, insert if not)"""
    try:
        cloudinary_url = cloudinary_result.get("secure_url", "")
        
        document = {
            "gender": gender,
            "label": label.lower(),
            "filename": image_path.name,
            "file_extension": image_path.suffix.lower(),
            "file_size": cloudinary_result.get("bytes", 0),
            "cloudinary_url": cloudinary_url,
            "cloudinary_public_id": cloudinary_result.get("public_id", ""),
            "cloudinary_folder": cloudinary_result.get("folder", ""),
            "image_width": cloudinary_result.get("width", 0),
            "image_height": cloudinary_result.get("height", 0),
            "uploaded_at": datetime.utcnow()
        }
        
        # Check if already exists
        existing = collection.find_one({
            "gender": gender,
            "label": label.lower(),
            "filename": image_path.name
        })
        
        if existing:
            # Update existing document with Cloudinary URL
            update_result = collection.update_one(
                {
                    "gender": gender,
                    "label": label.lower(),
                    "filename": image_path.name
                },
                {
                    "$set": {
                        "cloudinary_url": cloudinary_url,
                        "cloudinary_public_id": cloudinary_result.get("public_id", ""),
                        "cloudinary_folder": cloudinary_result.get("folder", ""),
                        "file_size": cloudinary_result.get("bytes", 0),
                        "image_width": cloudinary_result.get("width", 0),
                        "image_height": cloudinary_result.get("height", 0),
                        "uploaded_at": datetime.utcnow()
                    }
                }
            )
            if update_result.modified_count > 0:
                print(f"      ✅ Updated with Cloudinary URL!")
                return existing.get("_id")
            else:
                print(f"      ℹ️ Already has Cloudinary URL, no update needed")
                return existing.get("_id")
        
        # Insert new document
        result = collection.insert_one(document)
        return result.inserted_id
        
    except Exception as e:
        print(f"   ❌ MongoDB save error: {e}")
        return None

# ===========================================
# MAIN UPLOAD FUNCTION
# ===========================================

def upload_images_from_directory(
    collection,
    root_dir: str,
    gender: str
) -> Tuple[int, int]:
    """Upload 1 image from each subfolder in the root directory"""
    root_path = Path(root_dir)
    
    if not root_path.exists():
        print(f"⚠️ Directory not found: {root_dir}")
        return 0, 0
    
    print(f"\n📁 Processing {gender.upper()} images from: {root_dir}")
    print("-" * 60)
    
    # Get all subdirectories
    subdirs = [d for d in root_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not subdirs:
        print(f"   ⚠️ No subdirectories found in {root_dir}")
        return 0, 0
    
    uploaded_count = 0
    skipped_count = 0
    
    for subdir in sorted(subdirs):
        label = subdir.name
        print(f"\n   📂 Folder: {label}")
        
        # Get one image from this folder
        image_path = get_one_image_from_folder(subdir)
        
        if not image_path:
            print(f"      ⚠️ No images found in {label}")
            skipped_count += 1
            continue
        
        print(f"      📷 Selected: {image_path.name}")
        
        # Upload to Cloudinary
        print(f"      ☁️ Uploading to Cloudinary...", end=" ")
        cloudinary_result = upload_image_to_cloudinary(image_path, label, gender)
        
        if not cloudinary_result:
            print(f"❌ Failed!")
            skipped_count += 1
            continue
        
        cloudinary_url = cloudinary_result.get("secure_url", "")
        print(f"✅ Uploaded!")
        print(f"      🔗 URL: {cloudinary_url[:80]}...")
        
        # Save to MongoDB
        print(f"      💾 Saving to MongoDB...", end=" ")
        doc_id = save_to_mongodb(collection, image_path, label, gender, cloudinary_result)
        
        if doc_id:
            print(f"✅ Saved! (ID: {doc_id})")
            uploaded_count += 1
        else:
            print(f"⏭️ Skipped (duplicate or error)")
            skipped_count += 1
    
    return uploaded_count, skipped_count

# ===========================================
# MAIN
# ===========================================

def main():
    print("=" * 60)
    print("🚀 WearSmart - Cloudinary + MongoDB Uploader")
    print("=" * 60)
    
    # Setup Cloudinary
    if not setup_cloudinary():
        return
    
    # Connect to MongoDB
    client, collection = connect_to_mongodb()
    if client is None or collection is None:
        return
    
    # Upload men's images
    men_uploaded, men_skipped = upload_images_from_directory(
        collection, MEN_IMAGES_ROOT, "men"
    )
    
    # Upload women's images
    women_uploaded, women_skipped = upload_images_from_directory(
        collection, WOMEN_IMAGES_ROOT, "women"
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Upload Summary")
    print("=" * 60)
    print(f"   Men's images:   {men_uploaded} uploaded, {men_skipped} skipped")
    print(f"   Women's images: {women_uploaded} uploaded, {women_skipped} skipped")
    print(f"   Total uploaded: {men_uploaded + women_uploaded}")
    print("=" * 60)
    
    # Show sample query
    print("\n💡 Sample MongoDB Query:")
    print(f"   db.{COLLECTION_NAME}.find({{gender: 'men', label: 'shirt'}})")
    print(f"   db.{COLLECTION_NAME}.find({{cloudinary_url: {{$exists: true}}}})")
    
    # Close connection
    client.close()
    print("\n✅ Done! Connection closed.")

if __name__ == "__main__":
    main()

