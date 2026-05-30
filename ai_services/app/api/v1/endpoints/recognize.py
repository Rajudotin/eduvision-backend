"""
app/api/v1/endpoints/recognize.py
Face recognition endpoints with confidence tiers
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import cv2
import numpy as np
from app.core.face_recognizer import detector, recognizer

router = APIRouter()

def safe_float(value):
    """Convert numpy float to Python float"""
    if value is None:
        return 0.0
    return float(value)

@router.post("/face")
async def recognize_face(file: UploadFile = File(...)):
    """Recognize faces with confidence tiers"""
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise HTTPException(400, "Invalid image")
    
    faces = detector.get(img)
    
    auto_recognized = []
    uncertain_faces = []
    results = []
    
    for idx, face in enumerate(faces):
        result = recognizer.recognize_with_confidence(face['embedding'])
        
        # Convert all numpy values to Python types
        top_matches = []
        for match in result.get('top_matches', [])[:3]:
            top_matches.append({
                "student_id": str(match.get('student_id', '')),
                "similarity": safe_float(match.get('similarity', 0)),
                "confidence": safe_float(match.get('confidence', 0))
            })
        
        face_data = {
            "face_index": idx,
            "student_id": str(result['student_id']) if result['student_id'] else None,
            "confidence": safe_float(result['confidence']),
            "status": str(result.get('status', 'Unknown')),
            "is_match": bool(result.get('is_match', False)),
            "top_matches": top_matches
        }
        results.append(face_data)
        
        if result['is_match']:
            auto_recognized.append(face_data)
        elif safe_float(result['confidence']) >= 40 and top_matches:
            uncertain_faces.append({
                "face_index": idx,
                "suggested_student": top_matches[0]['student_id'],
                "confidence": safe_float(result['confidence']),
                "all_matches": top_matches
            })
    
    return {
        "faces_detected": len(faces),
        "recognized": len(auto_recognized),
        "uncertain_count": len(uncertain_faces),
        "auto_recognized": [r['student_id'] for r in auto_recognized],
        "uncertain_faces": uncertain_faces,
        "results": results
    }