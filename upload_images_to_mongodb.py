"""
Upload images from local directories to MongoDB Atlas
Uploads 1 image from each folder in clothing_images_men and clothing_images
"""

import os
import random
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import base64

try:
    from pymongo import MongoClient
    from gridfs import GridFS
    from bson import ObjectId
except ImportError:
    print("❌ pymongo not installed. Install it with: pip install pymongo")
    exit(1)

# ===========================================
# CONFIGURATION
# ===========================================

# MongoDB Atlas Connection String
# Format: mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
# Note: Special characters in password must be URL-encoded (! = %21, @ = %40, etc.)
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
# MONGODB CONNECTION
# ===========================================

def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    try:
        if MONGODB_URI == "YOUR_MONGODB_CONNECTION_STRING_HERE":
            print("❌ Please set your MongoDB connection string!")
            print("   Option 1: Set MONGODB_URI environment variable")
            print("   Option 2: Edit this script and replace MONGODB_URI")
            print("\n   Get your connection string from MongoDB Atlas:")
            print("   1. Go to your cluster")
            print("   2. Click 'Connect'")
            print("   3. Choose 'Connect your application'")
            print("   4. Copy the connection string")
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

def read_image_as_base64(image_path: Path) -> Optional[str]:
    """Read image file and convert to base64 string"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return base64_data
    except Exception as e:
        print(f"   ⚠️ Error reading {image_path.name}: {e}")
        return None

def upload_image_to_mongodb(
    collection,
    image_path: Path,
    label: str,
    gender: str,
    use_gridfs: bool = False
):
    """Upload image to MongoDB"""
    try:
        # Read image data
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Prepare document
        document = {
            "gender": gender,
            "label": label.lower(),
            "filename": image_path.name,
            "file_extension": image_path.suffix.lower(),
            "file_size": len(image_data),
            "uploaded_at": datetime.utcnow()
        }
        
        if use_gridfs:
            # Use GridFS for large files (better for MongoDB)
            fs = GridFS(collection.database)
            file_id = fs.put(
                image_data,
                filename=image_path.name,
                content_type=f"image/{image_path.suffix[1:].lower()}",
                gender=gender,
                label=label.lower()
            )
            document["gridfs_file_id"] = str(file_id)
            document["image_data"] = None  # Don't store in document if using GridFS
        else:
            # Store as base64 in document (simpler, but limited by 16MB document size)
            document["image_data"] = base64.b64encode(image_data).decode('utf-8')
            document["gridfs_file_id"] = None
        
        # Insert into collection
        result = collection.insert_one(document)
        return result.inserted_id
        
    except Exception as e:
        print(f"   ❌ Error uploading {image_path.name}: {e}")
        return None

# ===========================================
# MAIN UPLOAD FUNCTION
# ===========================================

def upload_images_from_directory(
    collection,
    root_dir: str,
    gender: str,
    use_gridfs: bool = False
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
        return 0
    
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
        
        # Check if already uploaded (optional - skip duplicates)
        existing = collection.find_one({
            "gender": gender,
            "label": label.lower(),
            "filename": image_path.name
        })
        
        if existing:
            print(f"      ⏭️ Already exists in database, skipping...")
            skipped_count += 1
            continue
        
        # Upload to MongoDB
        print(f"      ⬆️ Uploading...", end=" ")
        doc_id = upload_image_to_mongodb(collection, image_path, label, gender, use_gridfs)
        
        if doc_id:
            print(f"✅ Uploaded! (ID: {doc_id})")
            uploaded_count += 1
        else:
            print(f"❌ Failed!")
            skipped_count += 1
    
    return uploaded_count, skipped_count

# ===========================================
# MAIN
# ===========================================

def main():
    print("=" * 60)
    print("🚀 WearSmart - MongoDB Image Uploader")
    print("=" * 60)
    
    # Connect to MongoDB
    client, collection = connect_to_mongodb()
    if client is None or collection is None:
        return
    
    # Ask user preference for storage method
    print("\n📦 Storage Method:")
    print("   1. GridFS (Recommended for large files, better performance)")
    print("   2. Base64 in document (Simpler, but limited to 16MB per document)")
    
    choice = input("\n   Choose (1 or 2, default=1): ").strip()
    use_gridfs = choice != "2"
    
    if use_gridfs:
        print("   ✅ Using GridFS storage")
    else:
        print("   ✅ Using Base64 storage")
    
    # Upload men's images
    men_uploaded, men_skipped = upload_images_from_directory(
        collection, Path(MEN_IMAGES_ROOT), "men", use_gridfs
    )
    
    # Upload women's images
    women_uploaded, women_skipped = upload_images_from_directory(
        collection, Path(WOMEN_IMAGES_ROOT), "women", use_gridfs
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
    print(f"   db.{COLLECTION_NAME}.countDocuments()")
    
    # Close connection
    client.close()
    print("\n✅ Done! Connection closed.")

if __name__ == "__main__":
    main()

