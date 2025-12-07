# MongoDB Atlas Image Upload Guide

## 📋 Overview

This guide will help you upload images from your local directories (`clothing_images_men` and `clothing_images`) to MongoDB Atlas. The script uploads **1 image from each folder** to your MongoDB database.

---

## 🔧 Prerequisites

1. **MongoDB Atlas Account** - You already have this set up
2. **Connection String** - Get it from MongoDB Atlas
3. **Python Package** - Install pymongo

---

## 📦 Step 1: Install Required Package

```bash
pip install pymongo
```

Or add to your `requirements.txt`:
```
pymongo>=4.6.0
```

---

## 🔑 Step 2: Get Your MongoDB Connection String

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Navigate to your cluster (Cluster0)
3. Click **"Connect"** button
4. Choose **"Connect your application"**
5. Select **"Python"** and version **"3.12 or later"**
6. Copy the connection string

**Example connection string:**
```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

**Important:** Replace `<password>` with your actual database password!

---

## ⚙️ Step 3: Configure Connection String

You have **3 options** to set your MongoDB connection string:

### Option 1: Environment Variable (Recommended)

**Windows PowerShell:**
```powershell
$env:MONGODB_URI="mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/wearsmart?retryWrites=true&w=majority"
```

**Windows CMD:**
```cmd
set MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/wearsmart?retryWrites=true&w=majority
```

**Mac/Linux:**
```bash
export MONGODB_URI="mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/wearsmart?retryWrites=true&w=majority"
```

### Option 2: Edit the Script

Open `upload_images_to_mongodb.py` and replace:
```python
MONGODB_URI = os.getenv("MONGODB_URI", "YOUR_MONGODB_CONNECTION_STRING_HERE")
```

With:
```python
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/wearsmart?retryWrites=true&w=majority")
```

### Option 3: Enter When Prompted

The script will prompt you if no connection string is found.

---

## 🚀 Step 4: Run the Upload Script

```bash
python upload_images_to_mongodb.py
```

The script will:
1. Connect to MongoDB Atlas
2. Ask you to choose storage method (GridFS or Base64)
3. Scan `clothing_images_men` folder and upload 1 image from each subfolder
4. Scan `clothing_images` folder and upload 1 image from each subfolder
5. Show a summary of uploaded images

---

## 📊 Storage Methods

### GridFS (Recommended)
- Better for large files
- No 16MB document size limit
- Better performance for image storage
- Images stored separately from metadata

### Base64 in Document
- Simpler structure
- All data in one document
- Limited to 16MB per document
- Good for small images

**Recommendation:** Use GridFS for production.

---

## 📁 Database Structure

After uploading, your MongoDB documents will look like this:

### With GridFS:
```json
{
  "_id": ObjectId("..."),
  "gender": "men",
  "label": "shirt",
  "filename": "s1.jpg",
  "file_extension": ".jpg",
  "file_size": 123456,
  "gridfs_file_id": "507f1f77bcf86cd799439011",
  "image_data": null,
  "uploaded_at": ISODate("2024-01-01T00:00:00Z")
}
```

### With Base64:
```json
{
  "_id": ObjectId("..."),
  "gender": "men",
  "label": "shirt",
  "filename": "s1.jpg",
  "file_extension": ".jpg",
  "file_size": 123456,
  "image_data": "base64_encoded_string_here...",
  "gridfs_file_id": null,
  "uploaded_at": ISODate("2024-01-01T00:00:00Z")
}
```

---

## 🔍 Verify Upload

### In MongoDB Atlas Web UI:

1. Go to your cluster
2. Click **"Browse Collections"**
3. Select `wearsmart` database
4. Select `clothing_images` collection
5. You should see your uploaded documents

### Using MongoDB Queries:

**Count total documents:**
```javascript
db.clothing_images.countDocuments()
```

**Find all men's shirts:**
```javascript
db.clothing_images.find({gender: "men", label: "shirt"})
```

**Find all women's images:**
```javascript
db.clothing_images.find({gender: "women"})
```

**Get image by filename:**
```javascript
db.clothing_images.findOne({filename: "s1.jpg"})
```

---

## 🔄 Update FastAPI to Use MongoDB

After uploading, you can modify your FastAPI to fetch images from MongoDB instead of local files. Here's an example:

```python
from pymongo import MongoClient
from gridfs import GridFS
import base64
import os

# In your FastAPI app
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["wearsmart"]
collection = db["clothing_images"]
fs = GridFS(db)

@app.get("/images/mongodb")
def get_images_from_mongodb(
    gender: str = Query(..., pattern="^(men|women)$"),
    label: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
):
    """Get images from MongoDB"""
    # Find documents
    docs = list(collection.find({
        "gender": gender,
        "label": label.lower()
    }).limit(limit))
    
    images = []
    for doc in docs:
        if doc.get("gridfs_file_id"):
            # Retrieve from GridFS
            grid_file = fs.get(ObjectId(doc["gridfs_file_id"]))
            image_data = grid_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        else:
            # Get from document
            image_base64 = doc.get("image_data", "")
        
        images.append({
            "filename": doc["filename"],
            "label": doc["label"],
            "image_data": image_base64,
            "mime_type": f"image/{doc['file_extension'][1:]}"
        })
    
    return {"count": len(images), "items": images}
```

---

## ⚠️ Troubleshooting

### Error: "Failed to connect to MongoDB"

**Solutions:**
1. Check your connection string is correct
2. Ensure your IP address is whitelisted in MongoDB Atlas:
   - Go to "Network Access" in MongoDB Atlas
   - Click "Add IP Address"
   - Add your current IP or use `0.0.0.0/0` for all IPs (development only)
3. Verify username and password are correct
4. Check internet connection

### Error: "No images found"

**Solutions:**
1. Verify folders exist: `clothing_images_men` and `clothing_images`
2. Check subfolders contain image files (.jpg, .jpeg, .png, .webp)
3. Ensure you have read permissions for the folders

### Error: "pymongo not found"

**Solution:**
```bash
pip install pymongo
```

### Images not showing in MongoDB Atlas

**Solutions:**
1. Refresh the browser
2. Check the collection name is correct
3. Verify upload completed successfully (check script output)
4. Try querying: `db.clothing_images.find().limit(5)`

---

## 📝 Notes

1. **Duplicate Prevention:** The script checks if an image with the same filename and label already exists before uploading.

2. **Random Selection:** One random image is selected from each folder. Run the script multiple times to upload different images.

3. **File Size:** Be aware of MongoDB's 16MB document size limit if using Base64 storage. Use GridFS for larger files.

4. **Security:** Never commit your MongoDB connection string to version control. Use environment variables or `.env` files.

---

## 🎯 Next Steps

1. ✅ Upload images to MongoDB
2. ✅ Verify uploads in MongoDB Atlas
3. ✅ Update FastAPI to fetch from MongoDB (optional)
4. ✅ Test API endpoints with MongoDB data
5. ✅ Deploy to production

---

**Need Help?** Check the script output for detailed error messages and troubleshooting tips.

