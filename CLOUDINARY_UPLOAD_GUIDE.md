# Cloudinary + MongoDB Upload Guide

## 📋 Overview

This script uploads images from your local folders to **Cloudinary** (cloud storage) and stores the image URLs in **MongoDB Atlas**. This is better than storing images directly in MongoDB because:
- ✅ Faster image delivery
- ✅ Better scalability
- ✅ Image transformations available
- ✅ No MongoDB document size limits

---

## 🔧 Setup

### Step 1: Install Required Packages

```bash
pip install cloudinary python-dotenv pymongo
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

### Step 2: Get Cloudinary Credentials

1. Go to [Cloudinary Console](https://cloudinary.com/console)
2. Sign in or create a free account
3. Go to **Dashboard**
4. Copy your credentials:
   - **Cloud Name**
   - **API Key**
   - **API Secret**

### Step 3: Create .env File

Create a `.env` file in your project root:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
```

**Example:**
```env
CLOUDINARY_CLOUD_NAME=dbuu8ttbn
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=abcdefghijklmnopqrstuvwxyz123456
```

### Step 4: MongoDB Connection

Your MongoDB connection string is already configured in the script. If you need to change it, edit `upload_to_cloudinary_mongodb.py` or set the `MONGODB_URI` environment variable.

---

## 🚀 Usage

### Run the Upload Script

```bash
python upload_to_cloudinary_mongodb.py
```

### What It Does

1. ✅ Loads Cloudinary credentials from `.env` file
2. ✅ Connects to MongoDB Atlas
3. ✅ Scans `clothing_images_men` folder
4. ✅ Uploads **1 random image** from each subfolder to Cloudinary
5. ✅ Saves Cloudinary URL to MongoDB
6. ✅ Repeats for `clothing_images` folder (women's)
7. ✅ Shows upload summary

---

## 📊 Expected Output

```
============================================================
🚀 WearSmart - Cloudinary + MongoDB Uploader
============================================================
✅ Cloudinary configured successfully!
✅ Connected to MongoDB Atlas successfully!

📁 Processing MEN images from: clothing_images_men
------------------------------------------------------------

   📂 Folder: shirt
      📷 Selected: s1.jpg
      ☁️ Uploading to Cloudinary... ✅ Uploaded!
      🔗 URL: https://res.cloudinary.com/dbuu8ttbn/image/upload/v1234567890/wearsmart/men/shirt/s1.jpg...
      💾 Saving to MongoDB... ✅ Saved! (ID: 507f1f77bcf86cd799439011)

   📂 Folder: pants
      📷 Selected: p1.jpg
      ☁️ Uploading to Cloudinary... ✅ Uploaded!
      🔗 URL: https://res.cloudinary.com/dbuu8ttbn/image/upload/v1234567890/wearsmart/men/pants/p1.jpg...
      💾 Saving to MongoDB... ✅ Saved! (ID: 507f1f77bcf86cd799439012)

...

📊 Upload Summary
============================================================
   Men's images:   12 uploaded, 0 skipped
   Women's images: 10 uploaded, 0 skipped
   Total uploaded: 22
============================================================
```

---

## 📁 Cloudinary Folder Structure

Images are organized in Cloudinary as:
```
wearsmart/
  ├── men/
  │   ├── shirt/
  │   │   └── s1.jpg
  │   ├── pants/
  │   │   └── p1.jpg
  │   └── ...
  └── women/
      ├── shirts/
      │   └── s1.jpg
      └── ...
```

---

## 💾 MongoDB Document Structure

After uploading, your MongoDB documents will look like:

```json
{
  "_id": ObjectId("..."),
  "gender": "men",
  "label": "shirt",
  "filename": "s1.jpg",
  "file_extension": ".jpg",
  "file_size": 123456,
  "cloudinary_url": "https://res.cloudinary.com/dbuu8ttbn/image/upload/v1234567890/wearsmart/men/shirt/s1.jpg",
  "cloudinary_public_id": "wearsmart/men/shirt/s1",
  "cloudinary_folder": "wearsmart/men/shirt",
  "image_width": 800,
  "image_height": 600,
  "uploaded_at": ISODate("2024-01-01T00:00:00Z")
}
```

---

## 🔍 Verify Upload

### In Cloudinary Console

1. Go to [Cloudinary Media Library](https://cloudinary.com/console/media_library)
2. Navigate to `wearsmart/men/` or `wearsmart/women/`
3. You should see your uploaded images

### In MongoDB Atlas

1. Go to MongoDB Atlas → **Browse Collections**
2. Select `wearsmart` database
3. Select `clothing_images` collection
4. You should see documents with `cloudinary_url` field

### MongoDB Queries

**Find all men's shirts:**
```javascript
db.clothing_images.find({gender: "men", label: "shirt"})
```

**Get Cloudinary URLs only:**
```javascript
db.clothing_images.find({}, {cloudinary_url: 1, label: 1, gender: 1})
```

**Count images by gender:**
```javascript
db.clothing_images.aggregate([
  {$group: {_id: "$gender", count: {$sum: 1}}}
])
```

---

## 🔄 Update FastAPI to Use Cloudinary URLs

After uploading, update your FastAPI to fetch images from MongoDB and return Cloudinary URLs:

```python
from pymongo import MongoClient
import os

MONGODB_URI = os.getenv("MONGODB_URI", "your_connection_string")
client = MongoClient(MONGODB_URI)
db = client["wearsmart"]
collection = db["clothing_images"]

@app.get("/images/cloudinary")
def get_images_from_cloudinary(
    gender: str = Query(..., pattern="^(men|women)$"),
    label: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
):
    """Get images from MongoDB (Cloudinary URLs)"""
    docs = list(collection.find({
        "gender": gender,
        "label": label.lower()
    }).limit(limit))
    
    images = []
    for doc in docs:
        images.append({
            "filename": doc.get("filename", ""),
            "label": doc.get("label", ""),
            "url": doc.get("cloudinary_url", ""),
            "public_id": doc.get("cloudinary_public_id", ""),
            "width": doc.get("image_width", 0),
            "height": doc.get("image_height", 0)
        })
    
    return {"count": len(images), "items": images}
```

---

## 🎨 Cloudinary Image Transformations

You can use Cloudinary URLs with transformations:

**Original:**
```
https://res.cloudinary.com/dbuu8ttbn/image/upload/wearsmart/men/shirt/s1.jpg
```

**Resized to 300x300:**
```
https://res.cloudinary.com/dbuu8ttbn/image/upload/w_300,h_300,c_fill/wearsmart/men/shirt/s1.jpg
```

**Thumbnail:**
```
https://res.cloudinary.com/dbuu8ttbn/image/upload/w_200,h_200,c_thumb/wearsmart/men/shirt/s1.jpg
```

**Auto format (WebP if supported):**
```
https://res.cloudinary.com/dbuu8ttbn/image/upload/f_auto/wearsmart/men/shirt/s1.jpg
```

---

## ⚠️ Troubleshooting

### Error: "Cloudinary credentials not found"

**Solution:**
1. Check `.env` file exists in project root
2. Verify environment variable names are correct:
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
3. Install python-dotenv: `pip install python-dotenv`

### Error: "Invalid API credentials"

**Solution:**
1. Verify credentials in Cloudinary Console
2. Check for typos in `.env` file
3. Ensure no extra spaces in values

### Error: "Upload failed"

**Solution:**
1. Check internet connection
2. Verify image file exists and is readable
3. Check Cloudinary account limits (free tier has limits)
4. Verify file size (free tier: 10MB max per image)

### Images not showing in Cloudinary

**Solution:**
1. Check Cloudinary Media Library
2. Verify folder path: `wearsmart/gender/label/`
3. Check upload was successful (look at script output)

---

## 📝 Notes

1. **Free Tier Limits:**
   - 25 GB storage
   - 25 GB bandwidth/month
   - 10 MB max file size

2. **Duplicate Prevention:**
   - Script checks if image already exists before uploading
   - Uses filename + label + gender as unique identifier

3. **Random Selection:**
   - One random image is selected from each folder
   - Run multiple times to upload different images

4. **Security:**
   - Never commit `.env` file to Git
   - Add `.env` to `.gitignore`
   - Keep API secrets secure

---

## 🎯 Next Steps

1. ✅ Upload images to Cloudinary
2. ✅ Verify in Cloudinary Console
3. ✅ Verify in MongoDB Atlas
4. ✅ Update FastAPI to use Cloudinary URLs
5. ✅ Test API endpoints
6. ✅ Deploy to production

---

**Need Help?** Check Cloudinary [Documentation](https://cloudinary.com/documentation) or MongoDB [Atlas Documentation](https://www.mongodb.com/docs/atlas/).

