# test_cloudinary.py
"""
Test Cloudinary connection
"""
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

# Configure
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Test upload
def test_connection():
    try:
        # Get account info
        result = cloudinary.api.usage()
        print("✅ Cloudinary Connected!")
        print(f"   Plan: {result.get('plan', 'Free')}")
        print(f"   Storage Used: {result.get('storage', {}).get('usage', 0) / (1024*1024):.2f} MB")
        print(f"   Bandwidth Used: {result.get('bandwidth', {}).get('usage', 0) / (1024*1024):.2f} MB")
        print(f"   Credits Used: {result.get('credits', {}).get('usage', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()