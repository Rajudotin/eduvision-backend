# view_history.py
"""
View Attendance History Module
"""

import os
import json
from datetime import datetime

def view_history():
    """Display all attendance reports"""
    reports_dir = "data/attendance_logs"
    
    if not os.path.exists(reports_dir):
        print("\n📂 No attendance records found yet.")
        print("   Take some attendance first!")
        return
    
    report_files = [f for f in os.listdir(reports_dir) if f.endswith('.json')]
    
    if not report_files:
        print("\n📂 No attendance records found yet.")
        return
    
    # Sort by date (newest first)
    report_files.sort(reverse=True)
    
    print("\n" + "="*70)
    print("📊 ATTENDANCE HISTORY")
    print("="*70)
    
    for i, file in enumerate(report_files[:10], 1):  # Show last 10 reports
        filepath = os.path.join(reports_dir, file)
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        timestamp = datetime.fromisoformat(data['timestamp'])
        source = data.get('source', 'upload_photo')
        source_icon = "📸" if source == 'upload_photo' else "🎥"
        
        print(f"\n{i}. {source_icon} {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Source: {source.replace('_', ' ').title()}")
        print(f"   Present: {len(data['present_students'])}")
        print(f"   Absent: {len(data['absent_students'])}")
        print(f"   Unknown Faces: {data['unknown_faces']}")
        print(f"   Attendance Rate: {data['attendance_rate']:.1f}%")
        
        if data['present_students']:
            print(f"   Present: {', '.join(data['present_students'])}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    view_history()