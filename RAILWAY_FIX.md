# Railway Deployment Fix - Missing Files

## ❌ Current Issues

1. **Models Not Loading** - `weather_clothing_recommender.pkl` files are ignored by `.gitignore`
2. **Images Not Found** - Image folders are ignored (but you're using Cloudinary/MongoDB, so this is OK)

## ✅ Solution

### Step 1: Update .gitignore

I've updated `.gitignore` to allow model files to be committed:
- `!weather_clothing_recommender.pkl` - Exception for men's model
- `!weather_clothing_recommender_women.pkl` - Exception for women's model

### Step 2: Commit Model Files

```bash
# Add the model files
git add weather_clothing_recommender.pkl
git add weather_clothing_recommender_women.pkl

# Or add all files (git will respect .gitignore exceptions)
git add -A

# Commit
git commit -m "Add model files for Railway deployment"

# Push to GitHub
git push
```

### Step 3: Verify Files Are Committed

Check that the files are in your repository:
```bash
git ls-files | grep "\.pkl"
```

You should see:
- `weather_clothing_recommender.pkl`
- `weather_clothing_recommender_women.pkl`

### Step 4: Redeploy on Railway

Railway will automatically:
1. Detect the new commit
2. Rebuild with the model files
3. Models will load successfully

## 📝 About Images

**You DON'T need to commit image folders** because:
- You're using `/cloud-images` endpoint which fetches from MongoDB/Cloudinary
- Local images are only needed for `/images` endpoint (static files)
- For production, use Cloudinary URLs from MongoDB

## 🔍 Verify After Deployment

1. **Check Models Loaded:**
   ```
   GET https://wearsmart-model-production.up.railway.app/health
   ```
   Should show: `"men_model_loaded": true, "women_model_loaded": true`

2. **Test Recommendations:**
   ```
   POST https://wearsmart-model-production.up.railway.app/recommend/men
   ```
   Should work without 500 error

3. **Test Cloud Images:**
   ```
   GET https://wearsmart-model-production.up.railway.app/cloud-images?gender=men&label=hoodie&limit=5
   ```
   Should return Cloudinary URLs from MongoDB

## ⚠️ Important Notes

- **Model files are large** - Make sure they're under GitHub's file size limit (100MB)
- If models are too large, consider using Git LFS:
  ```bash
  git lfs install
  git lfs track "*.pkl"
  git add .gitattributes
  git add *.pkl
  git commit -m "Add model files with LFS"
  ```

- **Don't commit sensitive data** - Keep `.env` in `.gitignore`
- **MongoDB connection** - Already in code, but can override with Railway env vars

---

After committing and pushing, Railway will rebuild and your API should work! 🚀

