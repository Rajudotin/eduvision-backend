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

print('='*60)
print('CLOUDINARY - ALL UPLOADED FILES')
print('='*60)

try:
    result = cloudinary.api.resources(max_results=20)
    resources = result.get('resources', [])
    
    if not resources:
        print('No files found')
    else:
        print(f'Total files: {len(resources)}')
        for r in resources:
            print(f"  {r['public_id']}.{r['format']} | {r['bytes']/1024:.1f}KB")
            print(f"  URL: {r['secure_url']}")
            print()
except Exception as e:
    print(f'Error: {e}')

print('='*60)
print('View online: https://console.cloudinary.com/pm/media-library')
print('='*60)
