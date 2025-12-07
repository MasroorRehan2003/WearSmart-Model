# Model Compatibility Fix Guide

## ❌ The Problem

You're getting `KeyError: 118` which means:
- Your models were saved with a **different scikit-learn version** than what's installed
- Even though you have 1.6.1 locally, the models might have been saved with an older version
- Or there's a numpy/pandas version mismatch

## ✅ Solution Options

### Option 1: Re-save Models (RECOMMENDED)

Re-save your models with the current scikit-learn version:

```bash
# 1. Make sure you have the right version
pip install scikit-learn==1.6.1 joblib pandas numpy

# 2. Run the re-save script
python resave_models.py
```

This will:
- Create backups of your original models
- Load and re-save them with current scikit-learn 1.6.1
- Verify they can be loaded

**Then commit and push:**
```bash
git add weather_clothing_recommender.pkl weather_clothing_recommender_women.pkl
git commit -m "Re-save models with scikit-learn 1.6.1"
git push
```

### Option 2: Check What Version Was Used

Run the diagnostic script:

```bash
python check_model_version.py
```

This will tell you if the models can be loaded and what errors occur.

### Option 3: Retrain Models (Last Resort)

If re-saving doesn't work, you may need to retrain:

1. Use your original training script
2. Make sure scikit-learn==1.6.1 is installed
3. Train and save new models
4. Commit and push

## 🔍 Diagnostic Steps

### Step 1: Check Local Loading

```bash
python -c "import joblib; joblib.load('weather_clothing_recommender.pkl')"
```

If this fails locally, the model file itself has issues.

### Step 2: Check Versions

```bash
python -c "import sklearn, joblib, pandas, numpy; print(f'sklearn: {sklearn.__version__}, joblib: {joblib.__version__}, pandas: {pandas.__version__}, numpy: {numpy.__version__}')"
```

### Step 3: Try Re-saving

```bash
python resave_models.py
```

## 📝 What I've Updated

1. **requirements.txt** - Pinned all ML dependencies more strictly
2. **resave_models.py** - Script to re-save models with current version
3. **check_model_version.py** - Diagnostic script

## 🚀 After Fixing

1. Test locally:
   ```bash
   python -c "import joblib; m = joblib.load('weather_clothing_recommender.pkl'); print('✅ Model loads!')"
   ```

2. Commit the re-saved models:
   ```bash
   git add *.pkl
   git commit -m "Re-save models for compatibility"
   git push
   ```

3. Railway will auto-redeploy

4. Verify:
   ```bash
   curl https://wearsmart-model-production.up.railway.app/health
   ```

## ⚠️ Important Notes

- **Always backup** before re-saving (the script does this automatically)
- **Test locally** before pushing to Railway
- **Keep training scripts** so you can retrain if needed
- **Document versions** used for training

---

**The most likely fix: Run `python resave_models.py` and commit the new model files!**

