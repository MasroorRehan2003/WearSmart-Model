"""
Alternative approach: Try to load models with different scikit-learn versions
If re-saving doesn't work, we'll find what version was used and match it
"""

import subprocess
import sys
import os

def try_load_with_version(version):
    """Try to load model with a specific scikit-learn version"""
    print(f"\n🔍 Trying scikit-learn {version}...")
    
    # Create a test script
    test_script = f"""
import sys
try:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', f'scikit-learn=={version}'])
    import joblib
    import sklearn
    print(f"Installed scikit-learn: {{sklearn.__version__}}")
    
    # Try loading
    model = joblib.load('weather_clothing_recommender.pkl')
    print("✅ Model loaded successfully!")
    
    # Re-save
    joblib.dump(model, 'weather_clothing_recommender.pkl')
    print("✅ Model re-saved!")
    
    # Try women's model
    model2 = joblib.load('weather_clothing_recommender_women.pkl')
    joblib.dump(model2, 'weather_clothing_recommender_women.pkl')
    print("✅ Women's model re-saved!")
    
    print("\\n✅ SUCCESS! Both models re-saved.")
    sys.exit(0)
except KeyError as e:
    print(f"❌ KeyError {{e}} - version {version} doesn't work")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {{e}}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            capture_output=True,
            text=True,
            timeout=120
        )
        print(result.stdout)
        if result.returncode == 0:
            return True
        else:
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 Alternative Model Fix - Try Different Versions")
    print("=" * 60)
    
    # Common scikit-learn versions to try
    versions_to_try = [
        "1.3.2",  # Common older version
        "1.4.0",
        "1.4.1",
        "1.4.2",
        "1.5.0",
        "1.5.1",
        "1.5.2",
    ]
    
    print("\n📋 Will try these scikit-learn versions:")
    for v in versions_to_try:
        print(f"   - {v}")
    
    print("\n⏳ This may take a few minutes...")
    
    for version in versions_to_try:
        if try_load_with_version(version):
            print(f"\n✅ SUCCESS! Models work with scikit-learn {version}")
            print(f"\n📝 Update requirements.txt to:")
            print(f"   scikit-learn=={version}")
            print(f"\nThen commit and push:")
            print(f"   git add requirements.txt *.pkl")
            print(f"   git commit -m 'Fix models with scikit-learn {version}'")
            print(f"   git push")
            return
    
    print("\n❌ None of the common versions worked.")
    print("\n💡 Alternative solutions:")
    print("   1. Check your training script - what scikit-learn version did you use?")
    print("   2. Retrain the models with scikit-learn 1.6.1")
    print("   3. Use the original training environment to re-save")

if __name__ == "__main__":
    main()

