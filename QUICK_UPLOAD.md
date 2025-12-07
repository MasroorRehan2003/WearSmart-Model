# Quick Upload Guide - MongoDB Atlas

## 🚀 Quick Start (3 Steps)

### Step 1: Install pymongo
```bash
pip install pymongo
```

### Step 2: Get MongoDB Connection String
1. Go to MongoDB Atlas → Your Cluster → **Connect**
2. Choose **"Connect your application"**
3. Copy the connection string
4. Replace `<password>` with your actual password

### Step 3: Run Upload Script

**Option A: Set environment variable (Windows PowerShell)**
```powershell
$env:MONGODB_URI="mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/wearsmart?retryWrites=true&w=majority"
python upload_images_to_mongodb.py
```

**Option B: Edit script directly**
1. Open `upload_images_to_mongodb.py`
2. Find line: `MONGODB_URI = os.getenv("MONGODB_URI", "YOUR_MONGODB_CONNECTION_STRING_HERE")`
3. Replace with your connection string
4. Run: `python upload_images_to_mongodb.py`

**Option C: Enter when prompted**
Just run the script and enter the connection string when asked.

---

## ✅ What the Script Does

1. ✅ Connects to MongoDB Atlas
2. ✅ Scans `clothing_images_men` folder
3. ✅ Uploads **1 random image** from each subfolder
4. ✅ Scans `clothing_images` folder  
5. ✅ Uploads **1 random image** from each subfolder
6. ✅ Shows upload summary

---

## 📊 Expected Output

```
🚀 WearSmart - MongoDB Image Uploader
============================================================
✅ Connected to MongoDB Atlas successfully!

📦 Storage Method:
   1. GridFS (Recommended for large files, better performance)
   2. Base64 in document (Simpler, but limited to 16MB per document)

   Choose (1 or 2, default=1): 1
   ✅ Using GridFS storage

📁 Processing MEN images from: clothing_images_men
------------------------------------------------------------

   📂 Folder: shirt
      📷 Selected: s1.jpg
      ⬆️ Uploading... ✅ Uploaded! (ID: 507f1f77bcf86cd799439011)

   📂 Folder: pants
      📷 Selected: p1.jpg
      ⬆️ Uploading... ✅ Uploaded! (ID: 507f1f77bcf86cd799439012)

...

📊 Upload Summary
============================================================
   Men's images:   12 uploaded, 0 skipped
   Women's images: 10 uploaded, 0 skipped
   Total uploaded: 22
============================================================
```

---

## 🔍 Verify in MongoDB Atlas

1. Go to MongoDB Atlas → **Browse Collections**
2. Select `wearsmart` database
3. Select `clothing_images` collection
4. You should see your uploaded documents!

---

## ⚠️ Common Issues

**"Failed to connect"**
- ✅ Check connection string is correct
- ✅ Whitelist your IP in MongoDB Atlas (Network Access)
- ✅ Verify username/password

**"No images found"**
- ✅ Check folders exist: `clothing_images_men` and `clothing_images`
- ✅ Ensure subfolders contain image files

**"pymongo not found"**
- ✅ Run: `pip install pymongo`

---

For detailed instructions, see `MONGODB_UPLOAD_GUIDE.md`

