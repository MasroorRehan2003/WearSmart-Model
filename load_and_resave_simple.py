"""
Simple script to load and re-save models
Tries to handle version mismatches more gracefully
"""

import joblib
import sklearn
import sys
import os
import shutil
from datetime import datetime

print("=" * 60)
print("🔄 Simple Model Re-save")
print("=" * 60)

print(f"\nCurrent versions:")
print(f"  Python: {sys.version.split()[0]}")
print(f"  scikit-learn: {sklearn.__version__}")
print(f"  joblib: {joblib.__version__}")

# Check if files exist
men_file = "weather_clothing_recommender.pkl"
women_file = "weather_clothing_recommender_women.pkl"

if not os.path.exists(men_file):
    print(f"\n❌ File not found: {men_file}")
    sys.exit(1)

if not os.path.exists(women_file):
    print(f"\n❌ File not found: {women_file}")
    sys.exit(1)

# Create backups
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_men = f"weather_clothing_recommender_backup_{timestamp}.pkl"
backup_women = f"weather_clothing_recommender_women_backup_{timestamp}.pkl"

print(f"\n📦 Creating backups...")
shutil.copy(men_file, backup_men)
shutil.copy(women_file, backup_women)
print(f"   ✅ {backup_men}")
print(f"   ✅ {backup_women}")

# Try to load and re-save
print(f"\n🔄 Attempting to load and re-save...")

try:
    print(f"\n   Loading {men_file}...")
    men_model = joblib.load(men_file)
    print(f"   ✅ Loaded successfully")
    
    print(f"   Re-saving {men_file}...")
    joblib.dump(men_model, men_file)
    print(f"   ✅ Re-saved successfully")
    
except KeyError as e:
    print(f"   ❌ KeyError: {e}")
    print(f"   ⚠️ Cannot load with current scikit-learn version")
    print(f"   💡 Try running: python fix_models_alternative.py")
    sys.exit(1)
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    print(f"   💡 Try running: python fix_models_alternative.py")
    sys.exit(1)

try:
    print(f"\n   Loading {women_file}...")
    women_model = joblib.load(women_file)
    print(f"   ✅ Loaded successfully")
    
    print(f"   Re-saving {women_file}...")
    joblib.dump(women_model, women_file)
    print(f"   ✅ Re-saved successfully")
    
except KeyError as e:
    print(f"   ❌ KeyError: {e}")
    print(f"   ⚠️ Cannot load with current scikit-learn version")
    print(f"   💡 Try running: python fix_models_alternative.py")
    sys.exit(1)
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    print(f"   💡 Try running: python fix_models_alternative.py")
    sys.exit(1)

# Verify
print(f"\n✅ Verification...")
try:
    test_men = joblib.load(men_file)
    test_women = joblib.load(women_file)
    print(f"   ✅ Both models verified and working!")
    
    print(f"\n📝 Next steps:")
    print(f"   1. Test: python -c \"import joblib; joblib.load('{men_file}')\"")
    print(f"   2. Commit: git add *.pkl")
    print(f"   3. Push: git push")
    
except Exception as e:
    print(f"   ❌ Verification failed: {e}")
    print(f"   💡 Restore backups and try alternative method")
    sys.exit(1)

