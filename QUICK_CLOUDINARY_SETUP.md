# Quick Cloudinary Setup

## 🚀 3 Steps to Upload

### Step 1: Install Packages
```bash
pip install cloudinary python-dotenv
```

### Step 2: Create .env File

Create a file named `.env` in your project root with:

```env
CLOUDINARY_CLOUD_NAME=dbuu8ttbn
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
```

**Get credentials from:** https://cloudinary.com/console → Dashboard

### Step 3: Run Script
```bash
python upload_to_cloudinary_mongodb.py
```

---

## ✅ What It Does

1. Uploads 1 image from each folder in `clothing_images_men`
2. Uploads 1 image from each folder in `clothing_images`
3. Stores Cloudinary URLs in MongoDB Atlas
4. Shows upload summary

---

## 📋 Your Setup

- **MongoDB:** Already configured ✅
- **Cloudinary:** Need to add credentials to `.env` file
- **Script:** `upload_to_cloudinary_mongodb.py` ✅

---

## 🔍 Verify

**Cloudinary:** https://cloudinary.com/console/media_library
**MongoDB:** MongoDB Atlas → Browse Collections → `wearsmart` → `clothing_images`

---

For detailed instructions, see `CLOUDINARY_UPLOAD_GUIDE.md`

