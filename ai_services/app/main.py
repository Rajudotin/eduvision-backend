# api_service.py
# FastAPI entry point
"""
Face Recognition API Service - FastAPI
Exposes face recognition as REST endpoints
"""


from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import cv2
import numpy as np
import pickle
import os
from datetime import datetime
import uvicorn
from app.api.v1.router import api_router

# Import your existing face recognition module
from app.core.face_recognizer import detector, recognizer


app = FastAPI(title="Face Recognition API", version="1.0.0")

app.include_router(api_router, prefix="/api/v1")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class RegisterRequest(BaseModel):
    student_id: str
    student_name: str
    class_name: Optional[str] = None

class RegisterResponse(BaseModel):
    success: bool
    message: str
    student_id: str

class AttendanceRequest(BaseModel):
    class_name: str
    teacher_id: str

class AttendanceResponse(BaseModel):
    success: bool
    timestamp: str
    present_students: List[str]
    absent_students: List[str]
    attendance_rate: float

# ============ API Endpoints ============

@app.get("/")
def root():
    return {
        "service": "Face Recognition API",
        "status": "running",
        "version": "1.0.0",
        "registered_students": len(recognizer.database)
    }

@app.post("/api/register/face")
async def register_face(
    student_id: str,
    student_name: str,
    file: UploadFile = File(...)
):
    """
    Register a new student face
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Detect face
        faces = detector.get(img)
        
        if len(faces) == 0:
            raise HTTPException(status_code=400, detail="No face detected")
        
        # Use largest face
        face = max(faces, key=lambda f: (f['bbox'][2]-f['bbox'][0]) * (f['bbox'][3]-f['bbox'][1]))
        embedding = face['embedding']
        
        # Register
        recognizer.register_face(student_name, embedding, 1)
        recognizer.save_database()
        
        return {
            "success": True,
            "message": f"Student {student_name} registered successfully",
            "student_id": student_id,
            "student_name": student_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recognize")
async def recognize_faces(file: UploadFile = File(...)):
    """
    Recognize all faces in an image
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Detect faces
        faces = detector.get(img)
        
        results = []
        for face in faces:
            bbox = face['bbox'].astype(int).tolist()
            result = recognizer.recognize_with_confidence(face['embedding'])
            
            results.append({
                'bbox': bbox,
                'student_id': result['student_id'],
                'confidence': result['confidence'],
                'is_match': result['is_match'],
                'status': result['status']
            })
        
        return {
            'success': True,
            'total_faces': len(faces),
            'recognized_faces': [r for r in results if r['is_match']],
            'unknown_faces': [r for r in results if not r['is_match']],
            'results': results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/attendance/mark")
async def mark_attendance(
    class_name: str,
    file: UploadFile = File(...)
):
    """
    Mark attendance from group photo
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Detect and recognize faces
        faces = detector.get(img)
        
        present_students = []
        for face in faces:
            result = recognizer.recognize_with_confidence(face['embedding'])
            if result['is_match']:
                present_students.append(result['student_id'])
        
        # Remove duplicates
        present_students = list(set(present_students))
        
        # Get all registered students
        all_students = recognizer.get_all_students()
        absent_students = [s for s in all_students if s not in present_students]
        
        attendance_rate = (len(present_students) / len(all_students)) * 100 if all_students else 0
        
        # Save attendance record
        attendance_record = {
            'timestamp': datetime.now().isoformat(),
            'class_name': class_name,
            'present_students': present_students,
            'absent_students': absent_students,
            'attendance_rate': attendance_rate,
            'total_students': len(all_students)
        }
        
        # Save to file (will move to MongoDB later)
        os.makedirs("data/attendance_api", exist_ok=True)
        filename = f"data/attendance_api/attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            import json
            json.dump(attendance_record, f, indent=2)
        
        return {
            'success': True,
            'timestamp': attendance_record['timestamp'],
            'class_name': class_name,
            'present_students': present_students,
            'absent_students': absent_students,
            'attendance_rate': attendance_rate,
            'total_students': len(all_students)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/students")
async def get_all_students():
    """Get all registered students"""
    return {
        'success': True,
        'total': len(recognizer.database),
        'students': recognizer.get_all_students()
    }

@app.delete("/api/students/{student_id}")
async def delete_student(student_id: str):
    """Delete a student from database"""
    if student_id in recognizer.database:
        del recognizer.database[student_id]
        recognizer.save_database()
        return {'success': True, 'message': f'Student {student_id} deleted'}
    else:
        raise HTTPException(status_code=404, detail='Student not found')


if __name__ == "__main__":
    # Load existing database
    recognizer.load_database()
    print(f"✅ API Service Started with {len(recognizer.database)} registered students")
    uvicorn.run(app, host="0.0.0.0", port=8000)