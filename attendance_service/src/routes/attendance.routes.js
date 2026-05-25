const express = require("express");
const axios = require("axios");
const FormData = require("form-data");
const multer = require("multer");
const { pool } = require("../config/db");

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage() });

// ==================== MARK ATTENDANCE FROM PHOTO ====================
router.post("/mark", upload.single("photo"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "Photo required" });
    }

    // Call Face Recognition Service
    const formData = new FormData();
    formData.append("file", req.file.buffer, "photo.jpg");

    const faceResponse = await axios.post(
      `${process.env.FACE_API_URL}/recognize/face`,
      formData,
      { headers: formData.getHeaders(), timeout: 60000 }
    );

    const data = faceResponse.data;
    const today = new Date().toISOString().split("T")[0];
    const marked = [];
    const skipped = [];

    // Get ONLY student IDs from MySQL
    const [studentUsers] = await pool.query(
      "SELECT student_id FROM users WHERE role = 'student'"
    );
    const studentIds = new Set(studentUsers.map(u => u.student_id));

    // Auto-mark high confidence matches — ONLY for students
    const autoRecognized = data.auto_recognized || [];
    
    for (const student of autoRecognized) {
      // Skip non-students (teachers/admins detected by face)
      if (!studentIds.has(student)) {
        console.log(`⚠️ Skipping ${student} - not a student`);
        skipped.push({ student_id: student, reason: "Not a student" });
        continue;
      }

      const matchResult = (data.results || []).find(r => r.student_id === student);
      const confidence = matchResult ? matchResult.confidence : 0;

      await pool.query(
        `INSERT INTO attendance (student_id, date, time, status, confidence_score, marked_by)
         VALUES (?, ?, CURTIME(), 'present', ?, 'face')
         ON DUPLICATE KEY UPDATE status = 'present', time = CURTIME(), confidence_score = ?`,
        [student, today, confidence, confidence]
      );
      marked.push(student);
      console.log(`✅ Marked: ${student} (${confidence.toFixed(1)}%)`);
    }

    res.json({
      success: true,
      total_faces: data.faces_detected,
      recognized: data.recognized,
      marked_attendance: marked,
      skipped_faces: skipped,
      uncertain_faces: data.uncertain_faces || [],
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error("Attendance error:", error.message);
    res.status(500).json({ error: "Failed to mark attendance" });
  }
});

// ==================== MANUAL ATTENDANCE MARK ====================
router.post("/manual-mark", async (req, res) => {
  try {
    const { student_id, marked_by = "manual", confidence = 0 } = req.body;
    const today = new Date().toISOString().split("T")[0];

    if (!student_id) {
      return res.status(400).json({ error: "student_id required" });
    }

    // Check if user exists and is a student
    const [userCheck] = await pool.query(
      "SELECT role FROM users WHERE student_id = ?",
      [student_id]
    );

    if (userCheck.length === 0) {
      return res.status(404).json({ error: "Student not found" });
    }

    if (userCheck[0].role !== 'student') {
      return res.status(400).json({ error: "Can only mark attendance for students" });
    }

    await pool.query(
      `INSERT INTO attendance (student_id, date, time, status, confidence_score, marked_by)
       VALUES (?, ?, CURTIME(), 'present', ?, ?)
       ON DUPLICATE KEY UPDATE status = 'present', time = CURTIME(), marked_by = ?`,
      [student_id, today, confidence, marked_by, marked_by]
    );

    res.json({ success: true, student_id, marked_by });

  } catch (error) {
    console.error("Manual mark error:", error.message);
    res.status(500).json({ error: "Manual mark failed" });
  }
});

// ==================== GET TODAY'S ATTENDANCE ====================
router.get("/today", async (req, res) => {
  try {
    const today = new Date().toISOString().split("T")[0];
    const [records] = await pool.query(
      `SELECT a.*, u.full_name 
       FROM attendance a 
       JOIN users u ON a.student_id = u.student_id 
       WHERE a.date = ?`,
      [today]
    );
    res.json({ date: today, count: records.length, records });
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch attendance" });
  }
});

// ==================== GET STUDENT ATTENDANCE ====================
router.get("/student/:student_id", async (req, res) => {
  try {
    const [records] = await pool.query(
      `SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC LIMIT 50`,
      [req.params.student_id]
    );

    const present = records.filter((r) => r.status === "present").length;
    const percentage = records.length > 0 ? ((present / records.length) * 100).toFixed(2) : 0;

    res.json({
      student_id: req.params.student_id,
      total_days: records.length,
      present_days: present,
      attendance_percentage: parseFloat(percentage),
      records,
    });
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch attendance" });
  }
});

module.exports = router;