const express = require('express');
const PDFDocument = require('pdfkit');
const ExcelJS = require('exceljs');
const { pool } = require('../config/db');

const router = express.Router();

// Generate PDF Report
router.get('/pdf/:student_id', async (req, res) => {
    try {
        const { student_id } = req.params;
        const { month, year } = req.query;

        // Get student info
        const [students] = await pool.query(
            'SELECT * FROM users WHERE student_id = ?',
            [student_id]
        );

        if (students.length === 0) {
            return res.status(404).json({ error: 'Student not found' });
        }

        const student = students[0];

        // Get attendance records
        let query = `SELECT * FROM attendance WHERE student_id = ?`;
        const params = [student_id];

        if (month && year) {
            query += ` AND MONTH(date) = ? AND YEAR(date) = ?`;
            params.push(month, year);
        }

        query += ` ORDER BY date DESC`;

        const [records] = await pool.query(query, params);

        // Calculate stats
        const total = records.length;
        const present = records.filter(r => r.status === 'present').length;
        const percentage = total > 0 ? (present / total * 100).toFixed(2) : 0;

        // Create PDF
        const doc = new PDFDocument();
        
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename=${student_id}_attendance.pdf`);
        
        doc.pipe(res);

        // Header
        doc.fontSize(24).text('EduVision', { align: 'center' });
        doc.fontSize(16).text('Attendance Report', { align: 'center' });
        doc.moveDown();
        
        // Student Info
        doc.fontSize(12).text(`Student ID: ${student.user_id}`);
        doc.text(`Name: ${student.full_name}`);
        doc.text(`Email: ${student.email}`);
        doc.text(`Generated: ${new Date().toLocaleDateString()}`);
        doc.moveDown();

        // Stats
        doc.fontSize(14).text('Statistics', { underline: true });
        doc.fontSize(12).text(`Total Days: ${total}`);
        doc.text(`Present Days: ${present}`);
        doc.text(`Absent Days: ${total - present}`);
        doc.text(`Attendance Percentage: ${percentage}%`);
        doc.moveDown();

        // Records Table
        doc.fontSize(14).text('Attendance Records', { underline: true });
        doc.moveDown(0.5);
        
        records.forEach(record => {
            const date = new Date(record.date).toLocaleDateString();
            const status = record.status.toUpperCase();
            const color = status === 'PRESENT' ? 'GREEN' : 'RED';
            
            doc.fontSize(11).fillColor(color).text(`${date}: ${status}`, { indent: 20 });
            doc.fillColor('black');
        });

        doc.end();

    } catch (error) {
        console.error('PDF error:', error);
        res.status(500).json({ error: 'Failed to generate PDF' });
    }
});

// Generate Excel Report
router.get('/excel/:student_id', async (req, res) => {
    try {
        const { student_id } = req.params;

        const [students] = await pool.query(
            'SELECT * FROM users WHERE student_id = ?',
            [student_id]
        );

        if (students.length === 0) {
            return res.status(404).json({ error: 'Student not found' });
        }

        const student = students[0];
        const [records] = await pool.query(
            'SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC',
            [student_id]
        );

        // Create Excel
        const workbook = new ExcelJS.Workbook();
        const worksheet = workbook.addWorksheet('Attendance');

        // Title
        worksheet.mergeCells('A1:D1');
        worksheet.getCell('A1').value = 'EduVision Attendance Report';
        worksheet.getCell('A1').font = { size: 16, bold: true };
        worksheet.getCell('A1').alignment = { horizontal: 'center' };

        // Student Info
        worksheet.addRow([]);
        worksheet.addRow(['Student ID', student.user_id]);
        worksheet.addRow(['Name', student.full_name]);
        worksheet.addRow(['Email', student.email]);
        worksheet.addRow(['Generated', new Date().toLocaleDateString()]);
        worksheet.addRow([]);

        // Headers
        worksheet.addRow(['Date', 'Time', 'Status', 'Confidence', 'Marked By']);
        worksheet.getRow(7).font = { bold: true };

        // Data
        records.forEach(record => {
            worksheet.addRow([
                new Date(record.date).toLocaleDateString(),
                record.time,
                record.status,
                record.confidence ? `${record.confidence}%` : '-',
                record.marked_by
            ]);
        });

        // Auto-fit columns
        worksheet.columns.forEach(column => {
            column.width = 20;
        });

        res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        res.setHeader('Content-Disposition', `attachment; filename=${student_id}_attendance.xlsx`);

        await workbook.xlsx.write(res);
        res.end();

    } catch (error) {
        console.error('Excel error:', error);
        res.status(500).json({ error: 'Failed to generate Excel' });
    }
});

// Get summary stats
router.get('/summary/:student_id', async (req, res) => {
    try {
        const { student_id } = req.params;

        const [records] = await pool.query(
            `SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
                MAX(date) as last_attendance,
                MIN(date) as first_attendance
             FROM attendance WHERE student_id = ?`,
            [student_id]
        );

        const stats = records[0];
        const percentage = stats.total > 0 ? (stats.present / stats.total * 100).toFixed(2) : 0;
        
        // Calculate days needed for 75%
        const targetPercentage = 75;
        let daysNeeded = 0;
        
        if (percentage < targetPercentage) {
            const currentPresent = stats.present || 0;
            const currentTotal = stats.total || 0;
            daysNeeded = Math.ceil((targetPercentage * currentTotal / 100 - currentPresent) / (1 - targetPercentage / 100));
            daysNeeded = Math.max(0, daysNeeded);
        }

        res.json({
            student_id,
            total_days: stats.total || 0,
            present_days: stats.present || 0,
            absent_days: stats.absent || 0,
            attendance_percentage: parseFloat(percentage),
            days_needed_for_75: daysNeeded,
            last_attendance: stats.last_attendance,
            first_attendance: stats.first_attendance,
            status: percentage >= 75 ? 'Good Standing' : 'Below Required'
        });

    } catch (error) {
        res.status(500).json({ error: 'Failed to get summary' });
    }
});

module.exports = router;