"""
app/api/v1/router.py
Main API router for v1
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, register, recognize
from app.api.v1.endpoints import health, register, recognize, attendance

# Add this line

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(register.router, prefix="/register", tags=["Registration"])
api_router.include_router(recognize.router, prefix="/recognize", tags=["Recognition"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])