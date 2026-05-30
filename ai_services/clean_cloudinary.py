import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv
import os

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

print("Cleaning Cloudinary profile images...")

try:
    # Delete all files in eduvision/profiles/
    result = cloudinary.api.delete_resources_by_prefix('eduvision/profiles/')
    deleted = result.get('deleted', {})
    counts = deleted.get('counts', {})
    total = counts.get('total', 0)
    print(f"✅ Deleted {total} profile images")
except Exception as e:
    print(f"⚠️ Could not bulk delete: {e}")
    print("Trying individual delete...")

print("✅ Cloudinary cleanup complete!")