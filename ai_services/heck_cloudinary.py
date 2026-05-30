import cloudinary
import cloudinary.api
from dotenv import load_dotenv
import os

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

print("\n" + "="*60)
print("☁️  CLOUDINARY - ALL UPLOADED FILES")
print("="*60)

try:
    result = cloudinary.api.resources(max_results=20)
    resources = result.get('resources', [])
    
    if not resources:
        print("\n📭 No files found in Cloudinary")
    else:
        print(f"\n📸 Total files: {len(resources)}")
        print("-"*60)
        
        for r in resources:
            pid = r.get('public_id', 'N/A')
            fmt = r.get('format', 'N/A')
            size_kb = r.get('bytes', 0) / 1024
            url = r.get('secure_url', 'N/A')
            
            print(f"📁 {pid}.{fmt}")
            print(f"   Size: {size_kb:.1f} KB")
            print(f"   URL:  {url}")
            print()
    
    # Also check specific folders
    print("="*60)
    print("📂 FOLDER-WISE BREAKDOWN")
    print("="*60)
    
    folders = ['eduvision/profiles', 'eduvision/faces', 'eduvision/attendance', 'eduvision/reports']
    
    for folder in folders:
        try:
            folder_result = cloudinary.api.resources(type='upload', prefix=folder, max_results=5)
            count = len(folder_result.get('resources', []))
            print(f"  📁 {folder}: {count} files")
        except:
            print(f"  📁 {folder}: 0 files (empty)")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("🌐 View online: https://console.cloudinary.com/pm/media-library")
print("="*60)