# Railway Environment Variables Setup

## 🔧 Required Environment Variables

For your Railway deployment to work, you need to set these environment variables in the Railway dashboard.

## 📝 Step-by-Step Setup

### 1. Go to Railway Dashboard

1. Open your project: https://railway.app
2. Click on your **WearSmart-Model** service
3. Go to **Variables** tab (or **Settings** → **Variables**)

### 2. Add Environment Variables

Click **"New Variable"** and add these:

#### Required: MongoDB Connection String

**Variable Name:** `MONGODB_URI`

**Variable Value:**
```
mongodb+srv://i211707_db_user:2103921@cluster0.124kx3o.mongodb.net/wearsmart?retryWrites=true&w=majority
```

**Why:** This connects your API to MongoDB Atlas for the `/cloud-images` endpoint.

---

#### Optional: Cloudinary Credentials (if using cloud images)

**Variable Name:** `CLOUDINARY_CLOUD_NAME`  
**Variable Value:** `dbuu8ttbn` (or your cloud name)

**Variable Name:** `CLOUDINARY_API_KEY`  
**Variable Value:** Your Cloudinary API key

**Variable Name:** `CLOUDINARY_API_SECRET`  
**Variable Value:** Your Cloudinary API secret

---

### 3. Save and Redeploy

After adding variables:
1. Click **"Save"** or **"Add"**
2. Railway will automatically redeploy
3. Wait for deployment to complete

### 4. Verify

Test the endpoints:

```bash
# Health check
curl https://wearsmart-model-production.up.railway.app/health

# Cloud images (should work now)
curl https://wearsmart-model-production.up.railway.app/cloud-images?gender=men&label=hoodie&limit=5
```

## 🔍 Troubleshooting

### MongoDB Connection Still Failing?

1. **Check IP Whitelist:**
   - Go to MongoDB Atlas → Network Access
   - Add `0.0.0.0/0` (allow all IPs) OR Railway's IP range
   - Click "Add IP Address"

2. **Verify Connection String:**
   - Check username: `i211707_db_user`
   - Check password: `2103921`
   - Check cluster: `cluster0.124kx3o.mongodb.net`

3. **Check Railway Logs:**
   - Go to Railway → Your Service → Logs
   - Look for MongoDB connection messages
   - Should see: `✅ MongoDB connected successfully`

### Models Still Not Loading?

1. **Check scikit-learn version:**
   - Your local: `1.6.1`
   - Railway should install: `1.6.1` (now pinned in requirements.txt)

2. **Verify model files are committed:**
   ```bash
   git ls-files | grep "\.pkl"
   ```
   Should show:
   - `weather_clothing_recommender.pkl`
   - `weather_clothing_recommender_women.pkl`

3. **Check Railway build logs:**
   - Look for model loading messages
   - Should see: `✅ Men's model loaded successfully`

## 📋 Quick Checklist

- [ ] `MONGODB_URI` environment variable set in Railway
- [ ] MongoDB Atlas IP whitelist includes Railway IPs (or 0.0.0.0/0)
- [ ] Model files committed to Git
- [ ] scikit-learn version matches (1.6.1)
- [ ] Railway deployment completed successfully
- [ ] `/health` endpoint shows models loaded
- [ ] `/cloud-images` endpoint works

---

**After setting environment variables, Railway will auto-redeploy and everything should work!** 🚀

