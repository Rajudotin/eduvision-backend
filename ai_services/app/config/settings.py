"""
config/settings.py
Centralized configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Face Recognition
    FACE_DETECTION_THRESHOLD: float = 0.5
    FACE_RECOGNITION_THRESHOLD: float = 0.6
    MIN_FACE_SIZE: int = 112
    MODEL_NAME: str = "buffalo_l"
    USE_GPU: bool = False
    
    # Paths
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = DATA_DIR / "models"
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    LOGS_DIR: Path = DATA_DIR / "logs"
    
    # Database (from .env)
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "eduvision"
    
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "eduvision"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Singleton instance
settings = Settings()

# Create required directories
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)