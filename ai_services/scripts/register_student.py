# register_student.py
"""
Student Registration Module - No GUI Windows Version
Equivalent to Colab Cell 4
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.face_recognizer import detector, recognizer
from app.core.face_recognizer import detector, recognizer
from tkinter import filedialog
import tkinter as tk

def select_image_file():
    """Open file dialog to select image"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    root.attributes('-topmost', True)  # Bring to front
    
    file_path = filedialog.askopenfilename(
        title="Select Face Image",
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.JPG"),
            ("All files", "*.*")
        ]
    )
    root.destroy()
    return file_path

def display_image_with_face(img, bbox, sample_num):
    """Display image with matplotlib (no OpenCV GUI)"""
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(8, 6))
    plt.imshow(img_rgb)
    
    # Draw rectangle
    rect = plt.Rectangle((bbox[0], bbox[1]), bbox[2]-bbox[0], bbox[3]-bbox[1], 
                          fill=False, edgecolor='green', linewidth=2)
    plt.gca().add_patch(rect)
    
    plt.title(f"Sample {sample_num}: Face Detected")
    plt.axis('off')
    plt.show()

def register_new_student():
    """
    Register a new student with face samples
    """
    print("\n" + "="*60)
    print("📝 STUDENT REGISTRATION")
    print("="*60)
    
    student_name = input("\n👤 Enter student name: ").strip()
    if not student_name:
        print("❌ Name cannot be empty")
        return False
    
    num_samples = 3
    print(f"\n📸 Registering: {student_name}")
    print(f"Please select {num_samples} different photos")
    print("Tip: Different angles (front, slight left, slight right) for better accuracy\n")
    
    embeddings = []
    
    for i in range(num_samples):
        print(f"\n📤 Select photo #{i+1}/{num_samples}:")
        input("Press ENTER to open file browser...")
        
        file_path = select_image_file()
        
        if not file_path:
            print(f"⚠️ No file selected for sample {i+1}, skipping...")
            continue
        
        # Read image
        img = cv2.imread(file_path)
        if img is None:
            print(f"❌ Could not read image: {file_path}")
            continue
        
        print(f"   Processing: {os.path.basename(file_path)}")
        
        # Detect faces
        faces = detector.get(img)
        
        if len(faces) == 0:
            print(f"⚠️ No face detected in this image, skipping...")
            continue
        elif len(faces) > 1:
            print(f"⚠️ Multiple faces detected, using largest face")
            face = max(faces, key=lambda f: (f['bbox'][2]-f['bbox'][0]) * (f['bbox'][3]-f['bbox'][1]))
        else:
            face = faces[0]
        
        # Get embedding
        embedding = face['embedding']
        embeddings.append(embedding)
        
        # Display detected face using matplotlib
        bbox = face['bbox'].astype(int)
        display_image_with_face(img, bbox, i+1)
        
        print(f"   ✅ Face detected and processed!")
    
    if len(embeddings) == 0:
        print("\n❌ No valid faces found. Registration failed.")
        return False
    
    # Average embeddings
    avg_embedding = np.mean(embeddings, axis=0)
    
    # Register
    recognizer.register_face(student_name, avg_embedding, len(embeddings))
    
    # Save database
    recognizer.save_database()
    
    print(f"\n✅ Successfully registered {student_name} with {len(embeddings)} samples")
    print(f"   Total registered students: {len(recognizer.database)}")
    
    # Show all registered students
    print("\n📋 Registered Students:")
    for sid in recognizer.get_all_students():
        print(f"   • {sid}")
    
    return True

def show_registered_students():
    """Display all registered students"""
    print("\n" + "="*60)
    print("📋 REGISTERED STUDENTS LIST")
    print("="*60)
    
    if len(recognizer.database) == 0:
        print("   No students registered yet")
    else:
        for i, sid in enumerate(recognizer.get_all_students(), 1):
            data = recognizer.database[sid]
            print(f"   {i}. {sid}")
            print(f"      - Samples: {data['num_samples']}")
            print(f"      - Registered: {data['registered_at'][:19]}")
    print("="*60)

if __name__ == "__main__":
    while True:
        print("\n" + "="*60)
        print("🎯 STUDENT REGISTRATION MENU")
        print("="*60)
        print("1. Register New Student")
        print("2. Show All Registered Students")
        print("3. Exit")
        print("="*60)
        
        choice = input("\nEnter your choice (1/2/3): ").strip()
        
        if choice == '1':
            register_new_student()
        elif choice == '2':
            show_registered_students()
        elif choice == '3':
            print("\n👋 Exiting registration module...")
            break
        else:
            print("❌ Invalid choice. Please try again.")
