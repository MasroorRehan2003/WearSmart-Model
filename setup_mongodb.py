"""
Quick setup script to test MongoDB connection and upload images
Run this to verify your connection and upload images
"""

import os
from upload_images_to_mongodb import (
    connect_to_mongodb,
    upload_images_from_directory,
    get_collection
)

def test_connection():
    """Test MongoDB connection"""
    print("=" * 60)
    print("🔍 Testing MongoDB Connection")
    print("=" * 60)
    
    client, collection = connect_to_mongodb()
    
    if client is not None and collection is not None:
        print("\n✅ Connection successful!")
        
        # Test query
        count = collection.count_documents({})
        print(f"📊 Current documents in collection: {count}")
        
        # Show sample documents
        sample = collection.find_one()
        if sample:
            print(f"\n📄 Sample document:")
            print(f"   Gender: {sample.get('gender', 'N/A')}")
            print(f"   Label: {sample.get('label', 'N/A')}")
            print(f"   Filename: {sample.get('filename', 'N/A')}")
        
        client.close()
        return True
    else:
        print("\n❌ Connection failed!")
        return False

def main():
    print("\n🚀 WearSmart MongoDB Setup")
    print("=" * 60)
    
    # Test connection first
    if not test_connection():
        print("\n❌ Cannot proceed without connection. Please check your connection string.")
        return
    
    # Ask if user wants to upload
    print("\n" + "=" * 60)
    response = input("\n📤 Do you want to upload images now? (y/n): ").strip().lower()
    
    if response != 'y':
        print("✅ Setup complete. Run 'python upload_images_to_mongodb.py' when ready to upload.")
        return
    
    # Proceed with upload
    print("\n" + "=" * 60)
    client, collection = connect_to_mongodb()
    
    if client is None or collection is None:
        return
    
    # Ask for storage method
    print("\n📦 Storage Method:")
    print("   1. GridFS (Recommended for large files)")
    print("   2. Base64 in document (Simpler)")
    choice = input("\n   Choose (1 or 2, default=1): ").strip()
    use_gridfs = choice != "2"
    
    # Upload images
    men_uploaded, men_skipped = upload_images_from_directory(
        collection, "clothing_images_men", "men", use_gridfs
    )
    
    women_uploaded, women_skipped = upload_images_from_directory(
        collection, "clothing_images", "women", use_gridfs
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Upload Summary")
    print("=" * 60)
    print(f"   Men's images:   {men_uploaded} uploaded, {men_skipped} skipped")
    print(f"   Women's images: {women_uploaded} uploaded, {women_skipped} skipped")
    print(f"   Total uploaded: {men_uploaded + women_uploaded}")
    print("=" * 60)
    
    client.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()

