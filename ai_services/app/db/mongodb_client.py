# connection pool
"""
app/db/mongodb_client.py
MongoDB operations for face embeddings
"""
import numpy as np
from datetime import datetime
from config.connections import db

class MongoDBClient:
    
    @staticmethod
    def save_embedding(student_id: str, embedding: np.ndarray, 
                       model_name: str = "buffalo_l", num_samples: int = 1) -> bool:
        """Save face embedding to MongoDB"""
        try:
            mongo_db = db.get_mongodb()
            
            doc = {
                "student_id": student_id,
                "embedding": embedding.tolist(),
                "embedding_model": model_name,
                "num_samples": num_samples,
                "updated_at": datetime.now(),
                "is_active": True
            }
            
            mongo_db.face_embeddings.update_one(
                {"student_id": student_id},
                {"$set": doc},
                upsert=True
            )
            
            print(f"   ✅ MongoDB: {student_id} embedding saved")
            return True
        except Exception as e:
            print(f"   ❌ MongoDB failed: {e}")
            return False
    
    @staticmethod
    def get_embedding(student_id: str) -> np.ndarray:
        """Get embedding for a student"""
        try:
            mongo_db = db.get_mongodb()
            doc = mongo_db.face_embeddings.find_one({"student_id": student_id})
            if doc and "embedding" in doc:
                return np.array(doc["embedding"])
        except Exception as e:
            print(f"   ❌ MongoDB get failed: {e}")
        return None
    
    @staticmethod
    def get_all_embeddings() -> dict:
        """Get all active embeddings"""
        try:
            mongo_db = db.get_mongodb()
            embeddings = {}
            for doc in mongo_db.face_embeddings.find({"is_active": True}):
                embeddings[doc["student_id"]] = np.array(doc["embedding"])
            return embeddings
        except Exception as e:
            print(f"   ❌ MongoDB get all failed: {e}")
            return {}
    
    @staticmethod
    def delete_embedding(student_id: str) -> bool:
        """Soft delete an embedding"""
        try:
            mongo_db = db.get_mongodb()
            mongo_db.face_embeddings.update_one(
                {"student_id": student_id},
                {"$set": {"is_active": False, "updated_at": datetime.now()}}
            )
            return True
        except:
            return False

print("✅ MongoDBClient ready!")