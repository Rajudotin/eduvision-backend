"""
app/services/registration_service.py
Complete registration with all databases
"""
import numpy as np
from config.connections import db

# Initialize connections when module loads
db.setup_mysql()
db.setup_mongodb()
db.setup_redis()

class RegistrationService:
    
    @staticmethod
    def save_to_mysql(student_id: str, full_name: str, email: str, phone: str) -> bool:
        try:
            conn = db.get_mysql_connection()
            if conn is None:
                print("   ❌ MySQL connection is None")
                return False
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (student_id, full_name, email, phone)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    full_name = VALUES(full_name),
                    email = VALUES(email),
                    phone = VALUES(phone)
            """, (student_id, full_name, email, phone))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"   ✅ MySQL: {student_id} saved")
            return True
        except Exception as e:
            print(f"   ❌ MySQL failed: {e}")
            return False
    
    @staticmethod
    def save_to_mongodb(student_id: str, embedding: np.ndarray, num_samples: int) -> bool:
        try:
            mongo_db = db.get_mongodb()
            if mongo_db is None:
                print("   ❌ MongoDB connection is None")
                return False
                
            from datetime import datetime
            doc = {
                "student_id": student_id,
                "embedding": embedding.tolist(),
                "num_samples": num_samples,
                "model": "buffalo_l",
                "is_active": True,
                "created_at": datetime.now()
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
    def save_to_redis(student_id: str) -> bool:
        try:
            redis_client = db.get_redis()
            if redis_client:
                redis_client.setex(f"student:{student_id}", 3600, "registered")
                print(f"   ✅ Redis: {student_id} cached")
                return True
            return False
        except Exception as e:
            print(f"   ⚠️ Redis failed: {e}")
            return False
    
    @staticmethod
    def complete_registration(student_id: str, full_name: str, email: str,
                              phone: str, embedding: np.ndarray, num_samples: int) -> dict:
        print(f"\n💾 Saving {student_id} to databases...")
        
        results = {
            "mysql": RegistrationService.save_to_mysql(student_id, full_name, email, phone),
            "mongodb": RegistrationService.save_to_mongodb(student_id, embedding, num_samples),
            "redis": RegistrationService.save_to_redis(student_id)
        }
        
        return {
            "success": results["mysql"] and results["mongodb"],
            "student_id": student_id,
            "databases": results
        }

print("✅ RegistrationService ready!")