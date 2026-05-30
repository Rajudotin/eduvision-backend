"""
app/core/face_recognizer.py
Face Recognition System - Core Module
Equivalent to Colab Cells 1, 2, 3
"""

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import pickle
import os

# ============ Cell 1: Initialize Face Detector ============
print("\n" + "="*50)
print("📷 INITIALIZING FACE DETECTOR")
print("="*50)

# Initialize InsightFace detector (CPU Mode - same as Colab)
detector = FaceAnalysis(
    name='buffalo_l',
    providers=['CPUExecutionProvider'],
    allowed_modules=['detection', 'recognition']
)

# Prepare detector
detector.prepare(
    ctx_id=-1,           # CPU mode (same as Colab)
    det_size=(640, 640),  # Detection size
    det_thresh=0.5        # Confidence threshold
)

print("✅ Face Detector Ready!")
print(f"   Model: buffalo_l")
print(f"   Detection Size: 640x640")
print(f"   Confidence Threshold: 0.5")
print(f"   Providers: CPUExecutionProvider")


# ============ Cell 2: Face Recognition Class ============
class SmartFaceRecognizer:
    """
    Face Recognition System with confidence scoring
    Same as Colab implementation
    """

    def __init__(self, threshold=0.50, min_confidence=0.60):
        self.threshold = threshold
        self.min_confidence = min_confidence
        self.database = {}
        print(f"🎯 Recognizer initialized | Threshold: {threshold} | Min Confidence: {min_confidence}")

    def register_face(self, student_id, embedding, num_samples=1):
        """Register a new student face AND save to pickle"""
        self.database[student_id] = {
            'embedding': np.array(embedding),
            'num_samples': num_samples,
            'registered_at': datetime.now().isoformat()
        }
        print(f"✅ Registered: {student_id} | Total students: {len(self.database)}")
        # Auto-save to pickle after each registration
        self.save_database()

    def recognize_with_confidence(self, query_embedding):
        """Recognize face with detailed confidence analysis"""
        if not self.database:
            return {
                'student_id': None,
                'confidence': 0.0,
                'status': 'Database empty',
                'is_match': False,
                'top_matches': []
            }

        query_embedding = np.array(query_embedding).reshape(1, -1)

        all_matches = []
        for student_id, data in self.database.items():
            stored_embedding = data['embedding'].reshape(1, -1)
            similarity = cosine_similarity(query_embedding, stored_embedding)[0][0]

            all_matches.append({
                'student_id': student_id,
                'similarity': similarity,
                'confidence': similarity * 100
            })

        all_matches.sort(key=lambda x: x['similarity'], reverse=True)
        best_match = all_matches[0] if all_matches else None

        is_match = False
        status = "Unknown"

        if best_match:
            distance = 1 - best_match['similarity']
            passes_threshold = distance < self.threshold
            passes_confidence = best_match['similarity'] > self.min_confidence

            if len(all_matches) > 1:
                margin = best_match['similarity'] - all_matches[1]['similarity']
                clear_winner = margin > 0.15
            else:
                clear_winner = True

            if passes_threshold and passes_confidence and clear_winner:
                is_match = True
                status = "Match found"
            elif not passes_threshold:
                status = "Below threshold"
            elif not passes_confidence:
                status = "Low confidence"
            elif not clear_winner:
                status = "Multiple possible matches"

        return {
            'student_id': best_match['student_id'] if is_match else None,
            'confidence': best_match['confidence'] if best_match else 0.0,
            'status': status,
            'is_match': is_match,
            'top_matches': all_matches[:3]
        }

    def get_all_students(self):
        """Return list of registered students"""
        return list(self.database.keys())

    def save_database(self, filepath="data/face_database.pkl"):
        """Save database to pickle file"""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self.database, f)
        print(f"💾 Database saved to {filepath}")

    def load_database(self, filepath="data/face_database.pkl"):
        """Load database from pickle file"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'rb') as f:
                    self.database = pickle.load(f)
                print(f"📂 Database loaded from {filepath}")
                print(f"   Loaded {len(self.database)} students")
                for sid in self.database.keys():
                    print(f"   • {sid}")
                return True
            except Exception as e:
                print(f"⚠️ Failed to load database: {e}")
                return False
        else:
            print(f"📂 No database found at {filepath}")
            return False


# ============ Initialize Recognizer ============
recognizer = SmartFaceRecognizer(threshold=0.50, min_confidence=0.60)


def load_database_on_startup():
    """Load face database from MongoDB - ALWAYS works"""
    try:
        import os
        from dotenv import load_dotenv
        from pymongo import MongoClient
        
        load_dotenv()
        
        uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        db_name = os.getenv('MONGODB_DB', 'eduvision')
        
        print(f"🔍 Connecting to MongoDB: {uri}")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        client.admin.command('ping')
        print("✅ MongoDB connected")
        
        # Load all active embeddings
        collection = db['face_embeddings']
        docs = collection.find({"is_active": True})
        docs = collection.find({})        
        count = 0
        for doc in docs:
            student_id = doc.get("student_id")
            embedding = doc.get("embedding")
            if student_id and embedding:
                recognizer.database[student_id] = {
                    'embedding': np.array(embedding),
                    'num_samples': doc.get("num_samples", 1),
                    'registered_at': str(doc.get("created_at", datetime.now().isoformat()))
                }
                count += 1
        
        client.close()
        
        if count > 0:
            print(f"📂 Loaded {count} students from MongoDB")
            for sid in recognizer.database.keys():
                print(f"   • {sid}")
            
            # Save backup to pickle
            os.makedirs('data', exist_ok=True)
            with open('data/face_database.pkl', 'wb') as f:
                pickle.dump(recognizer.database, f)
            print("💾 Backup saved to pickle")
        else:
            print("📂 No embeddings found in MongoDB")
            
    except Exception as e:
        print(f"❌ MongoDB load failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Last resort: try pickle
        if os.path.exists('data/face_database.pkl'):
            try:
                with open('data/face_database.pkl', 'rb') as f:
                    recognizer.database = pickle.load(f)
                print(f"📂 Loaded {len(recognizer.database)} from pickle backup")
            except:
                print("❌ Pickle also failed")
load_database_on_startup()

print("\n" + "="*50)
print("📊 RECOGNIZER STATUS")
print("="*50)
print(f"   Registered Students: {len(recognizer.database)}")
print(f"   Ready for registration and recognition!")
print("="*50 + "\n")