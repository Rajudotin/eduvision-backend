# utils/face_recognizer.py
"""
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
        """Register a new student face"""
        self.database[student_id] = {
            'embedding': np.array(embedding),
            'num_samples': num_samples,
            'registered_at': datetime.now().isoformat()
        }
        print(f"✅ Registered: {student_id} | Total students: {len(self.database)}")

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
                status = f"Below threshold"
            elif not passes_confidence:
                status = f"Low confidence"
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
        """Save database to file for later use"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self.database, f)
        print(f"💾 Database saved to {filepath}")
    
    def load_database(self, filepath="data/face_database.pkl"):
        """Load database from file"""
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                self.database = pickle.load(f)
            print(f"📂 Database loaded from {filepath}")
            print(f"   Loaded {len(self.database)} students")
            return True
        return False


# Initialize recognizer with optimal settings (same as Colab)
recognizer = SmartFaceRecognizer(threshold=0.50, min_confidence=0.60)

print("\n" + "="*50)
print("📊 RECOGNIZER STATUS")
print("="*50)
print(f"   Registered Students: {len(recognizer.database)}")
print(f"   Ready for registration and recognition!")
print("="*50 + "\n")