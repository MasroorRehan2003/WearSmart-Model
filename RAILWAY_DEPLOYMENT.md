# Railway Deployment Guide

## ❌ Why Build Was Timing Out

### Main Issues:

1. **Duplicate Dependencies** (Lines 30-39)
   - Had duplicate entries without version numbers
   - Caused pip to reinstall packages unnecessarily

2. **Heavy Optional Dependencies**
   - `torch>=2.0.0` - PyTorch is **VERY HEAVY** (~2-3GB download)
   - `transformers>=4.30.0` - Hugging Face transformers is also heavy (~500MB+)
   - These packages take 10-15+ minutes to install
   - **NOT NEEDED** for `wearsmart_api.py` (your main API file doesn't use them)

3. **Streamlit Uncommented**
   - Streamlit is not needed for API deployment
   - Adds unnecessary dependencies

### What I Fixed:

✅ **Removed all duplicates**
✅ **Commented out heavy dependencies** (torch, transformers)
✅ **Commented out Streamlit** (not needed for API)
✅ **Kept only essential packages** for the FastAPI API

## 📦 Current Requirements (Optimized for Railway)

Your `requirements.txt` now only includes:
- FastAPI core dependencies
- ML model dependencies (joblib, pandas, scikit-learn)
- Database (pymongo)
- Cloud storage (cloudinary)
- HTTP client (requests)

**Total install time: ~2-3 minutes** (instead of 15+ minutes)

## 🚀 Deployment Steps

### 1. Commit Changes

```bash
git add requirements.txt railway.json Procfile
git commit -m "Fix requirements.txt for Railway deployment"
git push
```

### 2. Railway Configuration

Railway will automatically:
- Detect Python project
- Install from `requirements.txt`
- Use `Procfile` or `railway.json` for start command

### 3. Environment Variables

In Railway dashboard, add these environment variables:

```
MONGODB_URI=mongodb+srv://i211707_db_user:2103921@cluster0.124kx3o.mongodb.net/wearsmart?retryWrites=true&w=majority
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 4. Verify Deployment

After deployment, check:
- Build logs should complete in ~2-3 minutes
- Service should be "Online"
- Visit your Railway URL to test endpoints

## 📝 Files Created

1. **railway.json** - Railway-specific configuration
2. **Procfile** - Start command for Railway
3. **requirements.txt** - Cleaned up (no duplicates, no heavy deps)

## ⚠️ Important Notes

- **Don't uncomment torch/transformers** unless you absolutely need them
- These are only needed for BLIP image captioning (not in main API)
- If you need them later, add them to a separate `requirements-dev.txt`

## 🔍 Troubleshooting

### Build Still Times Out?

1. Check Railway build logs
2. Ensure no heavy packages are being installed
3. Verify `requirements.txt` has no duplicates
4. Check Railway plan limits (free tier has time limits)

### API Not Starting?

1. Check Railway deploy logs
2. Verify `wearsmart_api.py` is the main file
3. Ensure PORT environment variable is set (Railway sets this automatically)
4. Check MongoDB connection string is correct

### Models Not Loading?

1. Ensure `.pkl` files are committed to Git
2. Check file paths in `wearsmart_api.py`
3. Verify models are in the root directory

---

**The build should now complete successfully!** 🎉

