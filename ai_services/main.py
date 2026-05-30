"""
run.py
Face Attendance System - CLI Menu
Place: P:\dev\EDVISION_26\backend\ai_services\run.py
"""

import os
import sys
import subprocess
import pickle
import json
from pathlib import Path

# Set base directory
BASE_DIR = Path(__file__).parent

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    """Show application banner"""
    print("="*60)
    print("   🎯 FACE ATTENDANCE SYSTEM 🎯")
    print("="*60)
    print("   Powered by InsightFace (buffalo_l)")
    print("   Same accuracy as Google Colab")
    print("="*60)

def view_registered_students():
    """View all registered students"""
    try:
        # UPDATED PATH: data folder in root
        db_path = BASE_DIR / "data" / "face_database.pkl"
        
        if db_path.exists():
            with open(db_path, 'rb') as f:
                database = pickle.load(f)
            
            print("\n" + "="*60)
            print("📋 REGISTERED STUDENTS")
            print("="*60)
            
            if len(database) == 0:
                print("   No students registered yet")
            else:
                for i, (sid, data) in enumerate(database.items(), 1):
                    print(f"   {i}. {sid}")
                    print(f"      - Samples: {data['num_samples']}")
                    print(f"      - Registered: {data['registered_at'][:19]}")
            print("="*60)
        else:
            print("\n📋 No students registered yet!")
            print("   Please register students first (Option 1)")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def view_attendance_history():
    """View attendance history"""
    # UPDATED PATH: data/attendance_logs
    reports_dir = BASE_DIR / "data" / "attendance_logs"
    
    if not reports_dir.exists():
        print("\n📂 No attendance records found yet.")
        print("   Take some attendance first!")
        return
    
    report_files = list(reports_dir.glob("*.json"))
    
    if not report_files:
        print("\n📂 No attendance records found yet.")
        return
    
    # Sort by date (newest first)
    report_files.sort(reverse=True)
    print("\n" + "="*70)
    print("📊 ATTENDANCE HISTORY")
    print("="*70)
    
    for i, filepath in enumerate(report_files[:10], 1):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            timestamp = data.get('timestamp', 'Unknown')
            source = data.get('source', 'upload_photo')
            source_icon = "📸" if source == 'upload_photo' else "🎥"
            
            print(f"\n{i}. {source_icon} {timestamp[:19]}")
            print(f"   Source: {source.replace('_', ' ').title()}")
            print(f"   Present: {len(data.get('present_students', []))}")
            print(f"   Absent: {len(data.get('absent_students', []))}")
            print(f"   Unknown Faces: {data.get('unknown_faces', 0)}")
            print(f"   Attendance Rate: {data.get('attendance_rate', 0):.1f}%")
        except Exception as e:
            print(f"\n{i}. ❌ Error reading {filepath.name}: {e}")
    
    print("\n" + "="*70)

def clear_database():
    """Clear the face database"""
    confirm = input("\n⚠️ Are you sure? This will delete ALL registered students! (yes/no): ")
    if confirm.lower() == 'yes':
        db_path = BASE_DIR / "data" / "face_database.pkl"
        if db_path.exists():
            db_path.unlink()  # Delete file
            print("✅ Database cleared successfully!")
        else:
            print("ℹ️ No database found")
    else:
        print("❌ Cancelled")

def main_menu():
    """Display main menu and handle user choice"""
    while True:
        clear_screen()
        show_banner()
        
        print("\n📋 MAIN MENU")
        print("-"*40)
        print("   1. 📝 Register New Student")
        print("   2. 📤 Upload Photo Attendance")
        print("   3. 🎥 Live Camera Attendance")
        print("   4. 📋 View Registered Students")
        print("   5. 📊 View Attendance History")
        print("   6. 🗑️ Clear Database (Reset)")
        print("   7. 🚀 Start FastAPI Server")  # NEW OPTION
        print("   0. ❌ Exit")
        print("-"*40)
        
        choice = input("\n👉 Enter your choice: ").strip()
        
        if choice == '1':
            print("\n📝 Launching Registration Module...")
            # UPDATED PATH
            script_path = BASE_DIR / "scripts" / "register_student.py"
            if script_path.exists():
                subprocess.run(['python', str(script_path)])
            else:
                print(f"❌ Script not found: {script_path}")
            input("\nPress Enter to continue...")
            
        elif choice == '2':
            print("\n📤 Launching Upload Attendance Module...")
            # UPDATED PATH
            script_path = BASE_DIR / "scripts" / "attendance_upload.py"
            if script_path.exists():
                subprocess.run(['python', str(script_path)])
            else:
                print(f"❌ Script not found: {script_path}")
            input("\nPress Enter to continue...")
            
        elif choice == '3':
            print("\n🎥 Launching Camera Attendance Module...")
            # UPDATED PATH - Check multiple locations
            script_paths = [
                BASE_DIR / "scripts" / "attendance_camera_fixed.py",
                BASE_DIR / "scripts" / "attendance_camera.py",
                BASE_DIR / "attendance_camera_fixed.py",
                BASE_DIR / "attendance_camera.py"
            ]
            
            found = False
            for script_path in script_paths:
                if script_path.exists():
                    subprocess.run(['python', str(script_path)])
                    found = True
                    break
            
            if not found:
                print("❌ Camera module not found!")
                print("   Please create attendance_camera_fixed.py in scripts/ folder")
            input("\nPress Enter to continue...")
            
        elif choice == '4':
            view_registered_students()
            input("\nPress Enter to continue...")
            
        elif choice == '5':
            view_attendance_history()
            input("\nPress Enter to continue...")
            
        elif choice == '6':
            clear_database()
            input("\nPress Enter to continue...")
        
        elif choice == '7':
            print("\n🚀 Starting FastAPI Server...")
            print("   API will be available at: http://localhost:8000")
            print("   Documentation: http://localhost:8000/docs")
            print("\n   Press Ctrl+C to stop the server")
            print("-"*50)
            
            # Start FastAPI
            import uvicorn
            uvicorn.run(
                "app.main:app",
                host="0.0.0.0",
                port=8000,
                reload=True
            )
            
        elif choice == '0':
            print("\n👋 Thank you for using Face Attendance System!")
            print("   Goodbye!")
            sys.exit(0)
            
        else:
            print("\n❌ Invalid choice! Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    # Ensure data directories exist
    (BASE_DIR / "data").mkdir(exist_ok=True)
    (BASE_DIR / "data" / "attendance_logs").mkdir(exist_ok=True)
    (BASE_DIR / "data" / "uploads").mkdir(exist_ok=True)
    
    main_menu()