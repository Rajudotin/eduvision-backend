"""
app/api/v1/endpoints/health.py
Health check endpoints
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "eduvision-ai",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/detailed")
async def detailed_health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "face_detector": "ready",
        "registered_students": 0,
        "timestamp": datetime.now().isoformat()
    }