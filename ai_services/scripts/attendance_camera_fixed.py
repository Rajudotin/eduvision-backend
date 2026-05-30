# attendance_camera_fixed.py
"""
Live Camera Attendance Module - No OpenCV GUI
Uses direct capture without display window
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.face_recognizer import detector, recognizer
from datetime import datetime
import json
import os
import time

def capture_from_camera_simple():
    """
    Capture photo from webcam without display window
    Uses multiple attempts to get best shot
    """
    print("\n" + "="*60)
    print("🎥 LIVE CAMERA ATTENDANCE")
    print("="*60)
    
    # Try to open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Could not open webcam. Please check:")
        print("   1. Webcam is connected")
        print("   2. No other application is using the camera")
        print("   3. Camera permissions are granted")
        return None
    
    print("\n📸 Camera opened successfully!")
    print("\n📋 Instructions:")
    print("   • Position the camera to see all faces clearly")
    print("   • Make sure good lighting")
    print("   • We will take 3 photos and pick the best one")
    print("\n⏳ Preparing camera...")
    
    # Wait for camera to warm up
    time.sleep(2)
    
    # Take multiple photos and pick best
    photos = []
    
    for attempt in range(3):
        print(f"\n📷 Taking photo {attempt + 1}/3...")
        
        # Give user time to pose
        for countdown in range(3, 0, -1):
            print(f"   {countdown}...", end=" ", flush=True)
            time.sleep(1)
        print("SMILE! 😊")
        
        ret, frame = cap.read()
        if ret:
            # Flip horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Detect faces to check quality
            faces = detector.get(frame)
            num_faces = len(faces)
            
            photos.append({
                'image': frame.copy(),
                'num_faces': num_faces,
                'attempt': attempt + 1
            })
            print(f"   ✅ Captured! Found {num_faces} face(s)")
        else:
            print(f"   ❌ Failed to capture")
    
    # Cleanup
    cap.release()
    
    if not photos:
        print("\n❌ No photos captured successfully")
        return None
    
    # Select best photo (most faces)
    best_photo = max(photos, key=lambda x: x['num_faces'])
    
    print(f"\n✨ Selected best photo (Attempt {best_photo['attempt']}) with {best_photo['num_faces']} faces")
    
    return best_photo['image']

def display_detection_result(img, faces_data):
    """Display image with detection results using matplotlib"""
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(16, 12))
    plt.imshow(img_rgb)
    
    for face in faces_data:
        bbox = face['bbox']
        color = face['color']
        label = face['label']
        
        # Draw rectangle
        rect = plt.Rectangle((bbox[0], bbox[1]), bbox[2]-bbox[0], bbox[3]-bbox[1], 
                              fill=False, edgecolor=color, linewidth=2)
        plt.gca().add_patch(rect)
        
        # Draw label
        plt.text(bbox[0], bbox[1]-5, label, fontsize=10, color=color,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
    
    plt.title(f"Detection Results: {len([f for f in faces_data if f['type']=='present'])} Present, "
              f"{len([f for f in faces_data if f['type']=='unknown'])} Unknown, "
              f"{len([f for f in faces_data if f['type']=='uncertain'])} Uncertain")
    plt.axis('off')
    plt.show()

def manual_verification_camera(uncertain_faces, img):
    """Manual verification for uncertain faces"""
    verified_students = []
    
    if not uncertain_faces:
        return verified_students
    
    print("\n" + "="*60)
    print(f"🔍 MANUAL VERIFICATION - {len(uncertain_faces)} UNCERTAIN FACE(S)")
    print("="*60)
    
    # Display image with all faces for context
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(14, 10))
    plt.imshow(img_rgb)
    
    for face in uncertain_faces:
        bbox = face['bbox']
        rect = plt.Rectangle((bbox[0], bbox[1]), bbox[2]-bbox[0], bbox[3]-bbox[1], 
                              fill=False, edgecolor='orange', linewidth=3)
        plt.gca().add_patch(rect)
        
        # Add face number
        plt.text(bbox[0], bbox[1]-10, f"Face #{face['index']+1}", fontsize=12, color='orange',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.8))
    
    plt.title("Uncertain Faces (Orange Boxes) - Need Verification")
    plt.axis('off')
    plt.show()
    
    for face in uncertain_faces:
        top_match = face['top_matches'][0]
        student_name = top_match['student_id']
        confidence = top_match['similarity'] * 100
        
        print(f"\n{'='*50}")
        print(f"Face #{face['index']+1} of {len(uncertain_faces)}")
        print(f"{'='*50}")
        print(f"🤔 System suggests: {student_name}")
        print(f"   Confidence: {confidence:.1f}%")
        print(f"   Status: {face['status']}")
        
        # Extract and display just the face region
        bbox = face['bbox']
        if bbox[1] >= 0 and bbox[3] <= img.shape[0] and bbox[0] >= 0 and bbox[2] <= img.shape[1]:
            face_roi = img[bbox[1]:bbox[3], bbox[0]:bbox[2]]
            if face_roi.size > 0:
                face_roi_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                plt.figure(figsize=(4, 4))
                plt.imshow(face_roi_rgb)
                plt.title(f"Face to verify")
                plt.axis('off')
                plt.show()
        
        # Get user input
        print("\nOptions:")
        print("   y / yes - Mark as PRESENT")
        print("   n / no  - Mark as UNKNOWN")
        print("   s / skip - Skip this face")
        
        while True:
            choice = input("\nYour choice (y/n/s): ").strip().lower()
            if choice in ['y', 'yes']:
                verified_students.append({
                    'student_id': student_name,
                    'confidence': confidence,
                    'verified': True
                })
                print(f"   ✅ {student_name} marked as PRESENT")
                break
            elif choice in ['n', 'no']:
                print(f"   ❌ Face marked as UNKNOWN")
                break
            elif choice in ['s', 'skip']:
                print(f"   ⏭️ Skipped")
                break
            else:
                print("   ❌ Invalid choice. Enter y, n, or s")
    
    return verified_students

def generate_camera_report(present_students, unknown_count, verified_students=None):
    """Generate final attendance report for camera"""
    if verified_students is None:
        verified_students = []
    
    all_present = present_students.copy()
    all_present.extend(verified_students)
    
    # Remove duplicates
    seen_ids = set()
    unique_present = []
    for s in all_present:
        sid = s['student_id']
        if sid not in seen_ids:
            seen_ids.add(sid)
            unique_present.append(s)
    
    total_registered = len(recognizer.database)
    present_ids = [s['student_id'] for s in unique_present]
    absent_ids = [s for s in recognizer.get_all_students() if s not in present_ids]
    
    print("\n" + "="*70)
    print("📋 FINAL ATTENDANCE REPORT (LIVE CAMERA)")
    print("="*70)
    print(f"📅 Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n✅ PRESENT STUDENTS ({len(unique_present)}/{total_registered}):")
    print("-"*50)
    for student in unique_present:
        verification = "🔍 Manual" if student.get('verified') else "🤖 Auto"
        print(f"   • {student['student_id']} - {student['confidence']:.1f}% ({verification})")
    
    if absent_ids:
        print(f"\n❌ ABSENT STUDENTS ({len(absent_ids)}):")
        print("-"*50)
        for sid in absent_ids:
            print(f"   • {sid}")
    else:
        print(f"\n🎉 ALL STUDENTS PRESENT! (100% Attendance)")
    
    print(f"\n❓ UNKNOWN FACES: {unknown_count}")
    
    print("\n" + "="*70)
    print("📊 STATISTICS")
    print("="*70)
    print(f"   Total Registered Students: {total_registered}")
    print(f"   Present Today: {len(unique_present)}")
    print(f"   Absent: {len(absent_ids)}")
    
    if total_registered > 0:
        attendance_rate = (len(unique_present) / total_registered) * 100
        print(f"   📈 Attendance Rate: {attendance_rate:.1f}%")
        if attendance_rate >= 75:
            print(f"   ✅ Status: Above minimum requirement (75%)")
        else:
            print(f"   ⚠️ Status: Below minimum requirement (75%)")
    
    print("="*70)
    
    # Save report to file
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'source': 'live_camera',
        'present_students': present_ids,
        'absent_students': absent_ids,
        'unknown_faces': unknown_count,
        'attendance_rate': attendance_rate if total_registered > 0 else 0
    }
    
    os.makedirs("data/attendance_logs", exist_ok=True)
    report_file = f"data/attendance_logs/attendance_camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    print(f"\n💾 Report saved to: {report_file}")

def process_camera_image(img):
    """Process camera image and return detection results"""
    faces = detector.get(img)
    print(f"\n👥 Detected {len(faces)} faces in the frame")
    
    present_students = []
    unknown_faces = []
    uncertain_faces = []
    faces_data = []
    
    for idx, face in enumerate(faces):
        bbox = face['bbox'].astype(int)
        result = recognizer.recognize_with_confidence(face['embedding'])
        
        face_info = {
            'index': idx,
            'bbox': bbox.tolist(),
            'embedding': face['embedding']
        }
        
        if result['is_match']:
            label = f"{result['student_id']} ({result['confidence']:.0f}%)"
            color = 'green'
            face_info['type'] = 'present'
            face_info['label'] = label
            face_info['color'] = color
            face_info['student_id'] = result['student_id']
            face_info['confidence'] = result['confidence']
            present_students.append({
                'student_id': result['student_id'],
                'confidence': result['confidence'],
                'verified': False
            })
        else:
            if result['top_matches'] and result['top_matches'][0]['similarity'] > 0.45:
                label = f"? {result['top_matches'][0]['student_id']}? ({result['top_matches'][0]['confidence']:.0f}%)"
                color = 'orange'
                face_info['type'] = 'uncertain'
                face_info['label'] = label
                face_info['color'] = color
                face_info['top_matches'] = result['top_matches']
                face_info['status'] = result['status']
                uncertain_faces.append(face_info)
            else:
                label = "Unknown"
                color = 'red'
                face_info['type'] = 'unknown'
                face_info['label'] = label
                face_info['color'] = color
                unknown_faces.append(face_info)
        
        faces_data.append(face_info)
    
    # Display results
    display_detection_result(img, faces_data)
    
    print(f"\n📊 Detection Summary:")
    print(f"   ✅ Present (Auto): {len(present_students)}")
    print(f"   ⚠️ Uncertain (Need verification): {len(uncertain_faces)}")
    print(f"   ❌ Unknown: {len(unknown_faces)}")
    
    return present_students, unknown_faces, uncertain_faces, faces_data

def run_camera_attendance():
    """Main function for camera attendance"""
    # Load existing database
    recognizer.load_database()
    
    if len(recognizer.database) == 0:
        print("⚠️ No students registered yet!")
        print("Please register students first using: python register_student.py")
        return
    
    # Capture from camera
    img = capture_from_camera_simple()
    
    if img is None:
        print("❌ No image captured. Exiting...")
        return
    
    # Process the captured image
    present_students, unknown_faces, uncertain_faces, _ = process_camera_image(img)
    
    # Manual verification for uncertain faces
    verified_students = []
    if uncertain_faces:
        verified_students = manual_verification_camera(uncertain_faces, img)
    
    # Generate final report
    generate_camera_report(present_students, len(unknown_faces), verified_students)

if __name__ == "__main__":
    run_camera_attendance()
