# POST /attendance
"""
app/api/v1/endpoints/attendance.py
Attendance marking endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import cv2
import numpy as np
from datetime import datetime
from app.core.face_recognizer import detector, recognizer
from app.services.attendance_service import AttendanceService

router = APIRouter()

@router.post("/mark")
async def mark_attendance(file: UploadFile = File(...)):
    """
    Mark attendance from uploaded classroom photo
    Detects all faces and marks present students
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(400, "Invalid image")
        
        # Detect all faces
        faces = detector.get(img)
        
        if len(faces) == 0:
            return {
                "success": False,
                "message": "No faces detected",
                "faces_detected": 0,
                "present": [],
                "unknown": 0
            }
        
        # Recognize each face
        present_students = []
        unknown_count = 0
        
        for face in faces:
            result = recognizer.recognize_with_confidence(face['embedding'])
            
            if result['is_match']:
                student_id = result['student_id']
                confidence = result['confidence']
                
                # Mark attendance in MySQL
                AttendanceService.mark_attendance(student_id, confidence, "face")
                present_students.append({
                    "student_id": student_id,
                    "confidence": confidence
                })
            else:
                unknown_count += 1
        
        return {
            "success": True,
            "faces_detected": len(faces),
            "present_count": len(present_students),
            "unknown_count": unknown_count,
            "present_students": present_students,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(500, f"Attendance marking failed: {str(e)}")

@router.get("/today")
async def get_today_attendance():
    """Get today's attendance records"""
    records = AttendanceService.get_today_attendance()
    
    return {
        "date": datetime.now().date().isoformat(),
        "total_present": len(records),
        "records": records
    }

@router.get("/student/{student_id}")
async def get_student_attendance(student_id: str):
    """Get attendance history for a student"""
    from config.connections import db
    db.setup_mysql()
    conn = db.get_mysql_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, time, status, confidence, marked_by
        FROM attendance
        WHERE student_id = %s
        ORDER BY date DESC, time DESC
        LIMIT 50
    """, (student_id,))
    
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Calculate statistics
    total_days = len(records)
    present_days = sum(1 for r in records if r['status'] == 'present')
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    return {
        "student_id": student_id,
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": total_days - present_days,
        "attendance_percentage": round(attendance_percentage, 2),
        "records": records
    }