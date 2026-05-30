"""
app/api/v1/endpoints/register.py
Student registration with ALL databases + Cloudinary (1 profile photo only)
"""
import os
from dotenv import load_dotenv
load_dotenv()

import cloudinary
import cloudinary.uploader

# Configure Cloudinary ONCE
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)
print(f"☁️ Cloudinary configured: {os.getenv('CLOUDINARY_CLOUD_NAME')}")

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import cv2
import numpy as np
from app.core.face_recognizer import detector, recognizer
from app.services.registration_service import RegistrationService

router = APIRouter()

@router.post("/face")
async def register_face(
    student_id: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    images: list[UploadFile] = File(...)
):
    """Register a student - Saves to ALL databases + 1 profile photo to Cloudinary"""
    
    print(f"\n📝 Registration started: {student_id} | {full_name} | Images: {len(images)}")
    
    if len(images) < 3:
        raise HTTPException(400, "At least 3 images required")
    
    embeddings = []
    profile_url = None
    
    for idx, image_file in enumerate(images):
        print(f"   🔄 Processing image {idx+1}/{len(images)}")
        contents = await image_file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print(f"   ⚠️ Image {idx+1} is invalid, skipping")
            continue
        
        faces = detector.get(img)
        if len(faces) == 0:
            print(f"   ⚠️ No face detected in image {idx+1}, skipping")
            continue
        
        face = max(faces, key=lambda f: (f['bbox'][2]-f['bbox'][0]) * (f['bbox'][3]-f['bbox'][1]))
        embeddings.append(face['embedding'])
        print(f"   ✅ Face detected in image {idx+1}")
        
        # ☁️ Upload ONLY FIRST image to Cloudinary as profile photo
        if idx == 0:
            print(f"   📸 Attempting Cloudinary upload for {student_id}...")
            try:
                result = cloudinary.uploader.upload(
                    contents,
                    folder=f"eduvision/profiles/{student_id}",
                    public_id=f"{student_id}_profile",
                    overwrite=True,
                    transformation=[{'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'}]
                )
                profile_url = result['secure_url']
                print(f"   ☁️ Profile photo uploaded: {profile_url}")
            except Exception as e:
                print(f"   ⚠️ Cloudinary upload failed: {e}")
    
    print(f"   📊 Valid faces found: {len(embeddings)}/3")
    
    if len(embeddings) < 3:
        raise HTTPException(400, f"Only {len(embeddings)} valid faces found. Need 3+")
    
    # Average embeddings
    avg_embedding = np.mean(embeddings, axis=0)
    
    # 1️⃣ LOCAL PICKLE
    recognizer.register_face(student_id, avg_embedding, len(embeddings))
    print(f"✅ Local: {student_id} saved to recognizer")
    
    # 2️⃣ MYSQL + MONGODB + REDIS
    try:
        db_result = RegistrationService.complete_registration(
            student_id=student_id,
            full_name=full_name,
            email=email if email else f"{student_id}@eduvision.com",
            phone=phone if phone else "NA",
            embedding=avg_embedding,
            num_samples=len(embeddings)
        )
        print(f"✅ Cloud DB: {db_result}")
    except Exception as e:
        print(f"⚠️ Cloud DB save failed: {e}")
        db_result = {"success": False, "databases": {}}
    
    # 3️⃣ Update MySQL with profile image URL
    if profile_url:
        try:
            from config.connections import db
            db.setup_mysql()
            conn = db.get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET image_url = %s WHERE student_id = %s",
                (profile_url, student_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            print(f"   ✅ Profile URL saved to MySQL: {profile_url}")
        except Exception as e:
            print(f"   ⚠️ MySQL URL update failed: {e}")
    else:
        print(f"   ⚠️ No profile_url to save (Cloudinary upload may have failed)")
    
    return {
        "success": True,
        "student_id": student_id,
        "full_name": full_name,
        "samples_used": len(embeddings),
        "local_registered": len(recognizer.database),
        "cloudinary_profile": profile_url,
        "cloud_databases": db_result.get("databases", {})
    }

# ==================== GET ENDPOINTS ====================

@router.get("/students")
async def list_students():
    """List from local recognizer"""
    return {
        "source": "local_recognizer",
        "total": len(recognizer.database),
        "students": list(recognizer.database.keys())
    }

@router.get("/students/db")
async def list_students_from_db():
    """List from MySQL database (with Cloudinary URLs)"""
    try:
        from config.connections import db
        db.setup_mysql()
        conn = db.get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, full_name, email, phone, image_url, department, branch, year_of_study, created_at FROM users ORDER BY created_at DESC")
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "source": "mysql",
            "total": len(students),
            "students": students
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/students/mongodb")
async def list_students_from_mongodb():
    """List from MongoDB"""
    try:
        from config.connections import db
        db.setup_mongodb()
        mongo = db.get_mongodb()
        
        students = []
        for doc in mongo.face_embeddings.find({}):
            students.append({
                "student_id": doc.get("student_id"),
                "num_samples": doc.get("num_samples"),
                "model": doc.get("embedding_model", "buffalo_l"),
                "created_at": str(doc.get("created_at", ""))
            })
        
        return {
            "source": "mongodb",
            "total": len(students),
            "students": students
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/students/cloudinary")
async def list_students_cloudinary():
    """List all profile images from Cloudinary"""
    try:
        result = cloudinary.api.resources(
            type='upload',
            prefix='eduvision/profiles',
            max_results=50
        )
        
        images = []
        for r in result.get('resources', []):
            images.append({
                "public_id": r.get('public_id'),
                "url": r.get('secure_url'),
                "size_kb": round(r.get('bytes', 0) / 1024, 1),
                "format": r.get('format'),
                "created_at": r.get('created_at')
            })
        
        return {
            "source": "cloudinary",
            "total": len(images),
            "images": images
        }
    except Exception as e:
        return {"error": str(e)}