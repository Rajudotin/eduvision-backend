
const express = require('express');
const axios = require('axios');
const { pool } = require('../config/db');
const TwilioService = require('../services/twilio.service');
const WhatsAppService= require("../services/whatsapp.service")

const router = express.Router();

// Webhook for incoming WhatsApp messages
router.post('/webhook', async (req, res) => {
    try {
        const { Body, From, ProfileName } = req.body;
        
        console.log(`📨 Message from ${From}: "${Body}"`);
        
        // Check if it's a reason reply
        if (Body.toUpperCase().startsWith('REASON:')) {
            const reason = Body.substring(7).trim();
            const phone = From.replace('whatsapp:', '');
            
            // Find student by phone
            const [students] = await pool.query(
                'SELECT student_id, full_name FROM users WHERE phone = ?',
                [phone]
            );
            
            if (students.length > 0) {
                const student = students[0];
                const today = new Date().toISOString().split('T')[0];
                
                // Update attendance with reason
                await pool.query(
                    `UPDATE attendance 
                     SET reason = ? 
                     WHERE student_id = ? AND date = ?`,
                    [reason, student.student_id, today]
                );
                
                console.log(`✅ Reason saved for ${student.student_id}: ${reason}`);
            }
        }
        
        res.send('<Response></Response>');
        
    } catch (error) {
        console.error('Webhook error:', error);
        res.status(500).send('Error');
    }
});

// Send absence alerts to all absent students today
router.post('/send-absence-alerts', async (req, res) => {
    try {
        const today = new Date().toISOString().split('T')[0];
        
        // Get today's attendance
        const response = await axios.get(
            `${process.env.ATTENDANCE_API_URL}/today`
        );
        
        const presentStudents = response.data.records.map(r => r.student_id);
        
        // Get all students
        const [allStudents] = await pool.query(
            'SELECT student_id, full_name, phone FROM users WHERE role = "student"'
        );
        
        // Find absent students
        const absentStudents = allStudents.filter(
            s => !presentStudents.includes(s.student_id)
        );
        
        // Send alerts
        const results = [];
        for (const student of absentStudents) {
            const result = await WhatsAppService.sendAbsenceAlert(
                student.phone,
                student.full_name,
                today
            );
            results.push({ student_id: student.student_id, ...result });
        }
        
        res.json({
            success: true,
            date: today,
            absent_count: absentStudents.length,
            alerts_sent: results.filter(r => r.success).length,
            results
        });
        
    } catch (error) {
        console.error('Alert error:', error);
        res.status(500).json({ error: 'Failed to send alerts' });
    }
});

// Send monthly report to a student
router.post('/send-monthly-report/:student_id', async (req, res) => {
    try {
        const { student_id } = req.params;
        
        // Get student info
        const [students] = await pool.query(
            'SELECT full_name, phone FROM users WHERE student_id = ?',
            [student_id]
        );
        
        if (students.length === 0) {
            return res.status(404).json({ error: 'Student not found' });
        }
        
        const student = students[0];
        
        // Get attendance stats (from Report Service)
        const statsResponse = await axios.get(
            `http://localhost:5003/api/reports/summary/${student_id}`
        );
        
        const stats = statsResponse.data;
        
        // Send report
        const result = await WhatsAppService.sendMonthlyReport(
            student.phone,
            student.full_name,
            {
                total_days: stats.total_days,
                present_days: stats.present_days,
                percentage: stats.attendance_percentage,
                days_needed: stats.days_needed_for_75
            }
        );
        
        res.json({ success: true, ...result });
        
    } catch (error) {
        console.error('Monthly report error:', error);
        res.status(500).json({ error: 'Failed to send report' });
    }
});

// Send monthly reports to all students
router.post('/send-all-monthly-reports', async (req, res) => {
    try {
        const [students] = await pool.query(
            'SELECT student_id FROM users WHERE role = "student"'
        );
        
        const results = [];
        for (const student of students) {
            try {
                const response = await axios.post(
                    `http://localhost:${process.env.PORT}/api/whatsapp/send-monthly-report/${student.student_id}`
                );
                results.push({ student_id: student.student_id, ...response.data });
            } catch (err) {
                results.push({ student_id: student.student_id, success: false });
            }
        }
        
        res.json({
            total: students.length,
            sent: results.filter(r => r.success).length,
            results
        });
        
    } catch (error) {
        res.status(500).json({ error: 'Failed to send reports' });
    }
});

module.exports = router;