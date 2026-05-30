"""
app/services/attendance_service.py
Attendance marking with MySQL storage
"""
from datetime import datetime
from config.connections import db

# Initialize MySQL connection
db.setup_mysql()

class AttendanceService:
    
    @staticmethod
    def mark_attendance(student_id: str, confidence: float = None, marked_by: str = "face") -> bool:
        """Mark attendance for a student"""
        try:
            conn = db.get_mysql_connection()
            if conn is None:
                print("   ❌ MySQL connection is None")
                return False
                
            cursor = conn.cursor()
            now = datetime.now()
            
            cursor.execute("""
                INSERT INTO attendance (student_id, date, time, status, confidence, marked_by)
                VALUES (%s, %s, %s, 'present', %s, %s)
            """, (student_id, now.date(), now.time(), confidence, marked_by))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"   ✅ Attendance marked for {student_id}")
            return True
        except Exception as e:
            print(f"   ❌ Attendance failed: {e}")
            return False
    
    @staticmethod
    def get_today_attendance() -> list:
        """Get today's attendance records"""
        try:
            conn = db.get_mysql_connection()
            if conn is None:
                return []
                
            cursor = conn.cursor()
            today = datetime.now().date()
            
            cursor.execute("""
                SELECT a.student_id, u.full_name, a.time, a.confidence
                FROM attendance a
                LEFT JOIN users u ON a.student_id = u.student_id
                WHERE a.date = %s
                ORDER BY a.time DESC
            """, (today,))
            
            records = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return records
        except Exception as e:
            print(f"   ❌ Get attendance failed: {e}")
            return []

print("✅ AttendanceService ready!")