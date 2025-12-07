"""
MongoDB Configuration Helper
Store your MongoDB connection string here or use environment variables
"""

import os
from pymongo import MongoClient
from gridfs import GridFS

# ===========================================
# MONGODB CONFIGURATION
# ===========================================

# Option 1: Set connection string directly (NOT RECOMMENDED for production)
# MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/wearsmart?retryWrites=true&w=majority"

# Option 2: Use environment variable (RECOMMENDED)
# Set it in your system or .env file:
# MONGODB_URI = os.getenv("MONGODB_URI")

# Option 3: Get from user input
def get_mongodb_uri():
    """Get MongoDB URI from environment or prompt user"""
    uri = os.getenv("MONGODB_URI")
    
    if not uri:
        print("\n📝 MongoDB Connection String Required")
        print("   Get it from MongoDB Atlas:")
        print("   1. Go to your cluster")
        print("   2. Click 'Connect'")
        print("   3. Choose 'Connect your application'")
        print("   4. Copy the connection string")
        print("   5. Replace <password> with your actual password")
        print("\n   Example: mongodb+srv://user:pass@cluster.mongodb.net/wearsmart?retryWrites=true&w=majority")
        uri = input("\n   Enter MongoDB URI (or press Enter to skip): ").strip()
    
    return uri

# Database and Collection names
DATABASE_NAME = "wearsmart"
COLLECTION_NAME = "clothing_images"

# ===========================================
# CONNECTION HELPERS
# ===========================================

def get_mongodb_client(uri: str = None):
    """Get MongoDB client connection"""
    if not uri:
        uri = get_mongodb_uri()
    
    if not uri:
        raise ValueError("MongoDB URI is required")
    
    try:
        client = MongoClient(uri)
        # Test connection
        client.admin.command('ping')
        return client
    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")

def get_database(uri: str = None):
    """Get database instance"""
    client = get_mongodb_client(uri)
    return client[DATABASE_NAME]

def get_collection(uri: str = None):
    """Get collection instance"""
    db = get_database(uri)
    return db[COLLECTION_NAME]

def get_gridfs(uri: str = None):
    """Get GridFS instance"""
    db = get_database(uri)
    return GridFS(db)

