const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const { MongoClient } = require("mongodb");
const cloudinary = require("cloudinary").v2;
const { pool, redisClient } = require("../config/db");

const router = express.Router();

const MONGO_URI = process.env.MONGODB_URI || "mongodb://localhost:27017";
const MONGO_DB = process.env.MONGODB_DB || "eduvision";

// Cloudinary config
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
  secure: true,
});

// ==================== REGISTER ====================
router.post("/register", async (req, res) => {
  try {
    const {
      student_id,
      full_name,
      email,
      phone,
      password,
      role = "student",
      department,
      branch,
      year_of_study,
    } = req.body;

    if (!student_id || !full_name || !email || !password) {
      return res.status(400).json({ error: "All fields are required" });
    }

    const [existing] = await pool.query(
      "SELECT id FROM users WHERE student_id = ? OR email = ?",
      [student_id, email],
    );
    if (existing.length > 0) {
      return res.status(400).json({ error: "User already exists" });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    await pool.query(
      `INSERT INTO users (student_id, full_name, email, phone, password_hash, role, department, branch, year_of_study, is_verified)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        student_id,
        full_name,
        email,
        phone,
        hashedPassword,
        role,
        department || null,
        branch || null,
        year_of_study || null,
        true,
      ],
    );

    const token = jwt.sign({ student_id, role }, process.env.JWT_SECRET, {
      expiresIn: process.env.JWT_EXPIRE || "7d",
    });

    if (redisClient && redisClient.isOpen) {
      await redisClient.setEx(
        `user:${student_id}`,
        3600,
        JSON.stringify({ student_id, role }),
      );
    }

    res.status(201).json({
      success: true,
      token,
      user: { student_id, full_name, email, role },
    });
  } catch (error) {
    console.error("Register error:", error);
    res.status(500).json({ error: "Registration failed: " + error.message });
  }
});

// ==================== LOGIN ====================
router.post("/login", async (req, res) => {
  try {
    const { student_id, password } = req.body;
    if (!student_id || !password)
      return res
        .status(400)
        .json({ error: "student_id and password required" });

    const [users] = await pool.query(
      "SELECT * FROM users WHERE student_id = ? OR email = ?",
      [student_id, student_id],
    );
    if (users.length === 0)
      return res.status(401).json({ error: "Invalid credentials" });

    const user = users[0];
    const isValid = await bcrypt.compare(password, user.password_hash || "");
    if (!isValid) return res.status(401).json({ error: "Invalid credentials" });

    const token = jwt.sign(
      { student_id: user.student_id, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRE || "7d" },
    );

    if (redisClient && redisClient.isOpen) {
      await redisClient.setEx(`session:${user.student_id}`, 86400, token);
    }

    // ✅ ADDED: image_url, department, branch, year_of_study
    res.json({
      success: true,
      token,
      user: {
        student_id: user.student_id,
        full_name: user.full_name,
        email: user.email,
        phone: user.phone,
        role: user.role,
        image_url: user.image_url,
        department: user.department,
        branch: user.branch,
        year_of_study: user.year_of_study,
      },
    });
  } catch (error) {
    console.error("Login error:", error);
    res.status(500).json({ error: "Login failed" });
  }
});

// ==================== LOGOUT ====================
router.post("/logout", async (req, res) => {
  try {
    const token = req.header("Authorization")?.replace("Bearer ", "");
    if (token && redisClient && redisClient.isOpen) {
      await redisClient.setEx(`blacklist:${token}`, 86400, "1");
    }
    res.json({ success: true, message: "Logged out successfully" });
  } catch (error) {
    res.status(500).json({ error: "Logout failed" });
  }
});

// ==================== GET ALL USERS ====================
router.get("/users", async (req, res) => {
  try {
    const { role, limit = 50 } = req.query;
    let query =
      "SELECT id, student_id, full_name, email, phone, role, department, branch, year_of_study, image_url, is_verified, created_at FROM users";
    let params = [];
    if (role) {
      query += " WHERE role = ?";
      params.push(role);
    }
    query += " ORDER BY created_at DESC LIMIT ?";
    params.push(parseInt(limit));
    const [users] = await pool.query(query, params);
    res.json({ success: true, total: users.length, users });
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch users" });
  }
});

// ==================== GET CURRENT USER ====================
router.get("/me", async (req, res) => {
  try {
    const token = req.header("Authorization")?.replace("Bearer ", "");
    if (!token) return res.status(401).json({ error: "No token provided" });

    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // ✅ FIXED: Added image_url, department, branch, year_of_study
    const [users] = await pool.query(
      "SELECT student_id, full_name, email, phone, role, department, branch, year_of_study, image_url, created_at FROM users WHERE student_id = ?",
      [decoded.student_id],
    );

    if (users.length === 0)
      return res.status(404).json({ error: "User not found" });
    res.json({ user: users[0] });
  } catch (error) {
    if (error.name === "JsonWebTokenError")
      return res.status(401).json({ error: "Invalid token" });
    if (error.name === "TokenExpiredError")
      return res.status(401).json({ error: "Token expired" });
    res.status(500).json({ error: "Failed to fetch user" });
  }
});

// ==================== UPDATE PROFILE ====================
router.put("/update-profile", async (req, res) => {
  try {
    const token = req.header("Authorization")?.replace("Bearer ", "");
    if (!token) return res.status(401).json({ error: "No token" });

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const { full_name, email, phone } = req.body;
    if (!full_name && !email && !phone)
      return res.status(400).json({ error: "No fields to update" });

    let updates = [],
      params = [];
    if (full_name) {
      updates.push("full_name = ?");
      params.push(full_name);
    }
    if (email) {
      updates.push("email = ?");
      params.push(email);
    }
    if (phone) {
      updates.push("phone = ?");
      params.push(phone);
    }
    params.push(decoded.student_id);

    await pool.query(
      `UPDATE users SET ${updates.join(", ")} WHERE student_id = ?`,
      params,
    );

    // ✅ FIXED: Added all fields
    const [users] = await pool.query(
      "SELECT student_id, full_name, email, phone, role, department, branch, year_of_study, image_url FROM users WHERE student_id = ?",
      [decoded.student_id],
    );
    res.json({ success: true, user: users[0] });
  } catch (error) {
    res.status(500).json({ error: "Update failed" });
  }
});

// ==================== CHANGE PASSWORD ====================
router.put("/change-password", async (req, res) => {
  try {
    const token = req.header("Authorization")?.replace("Bearer ", "");
    if (!token) return res.status(401).json({ error: "No token" });

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const { current_password, new_password } = req.body;
    if (!current_password || !new_password)
      return res
        .status(400)
        .json({ error: "Current and new password required" });
    if (new_password.length < 6)
      return res.status(400).json({ error: "Min 6 characters" });

    const [users] = await pool.query(
      "SELECT password_hash FROM users WHERE student_id = ?",
      [decoded.student_id],
    );
    if (users.length === 0)
      return res.status(404).json({ error: "User not found" });

    const isValid = await bcrypt.compare(
      current_password,
      users[0].password_hash,
    );
    if (!isValid)
      return res.status(401).json({ error: "Current password incorrect" });

    const hashedPassword = await bcrypt.hash(new_password, 10);
    await pool.query(
      "UPDATE users SET password_hash = ? WHERE student_id = ?",
      [hashedPassword, decoded.student_id],
    );

    res.json({ success: true, message: "Password changed successfully" });
  } catch (error) {
    res.status(500).json({ error: "Password change failed" });
  }
});

// ==================== DELETE USER (MySQL + MongoDB + Cloudinary) ====================
router.delete("/user/:student_id", async (req, res) => {
  const { student_id } = req.params;
  let mongoClient;

  try {
    // 1. Delete from MySQL
    const [result] = await pool.query(
      "DELETE FROM users WHERE student_id = ?",
      [student_id],
    );
    if (result.affectedRows === 0)
      return res.status(404).json({ error: "User not found" });

    // 2. Delete from MongoDB
    try {
      mongoClient = await MongoClient.connect(MONGO_URI);
      const db = mongoClient.db(MONGO_DB);
      await db.collection("face_embeddings").deleteOne({ student_id });
      console.log(`✅ MongoDB: Deleted embedding for ${student_id}`);
    } catch (e) {
      console.warn("⚠️ MongoDB delete failed:", e.message);
    }

    // 3. Delete from Cloudinary
    try {
      const publicId = `eduvision/profiles/${student_id}/${student_id}_profile`;
      await cloudinary.uploader.destroy(publicId);
      console.log(`✅ Cloudinary: Deleted ${publicId}`);
    } catch (e) {
      console.warn("⚠️ Cloudinary delete failed:", e.message);
    }

    // 4. Delete from Redis
    try {
      if (redisClient && redisClient.isOpen) {
        await redisClient.del(`user:${student_id}`);
        await redisClient.del(`session:${student_id}`);
      }
    } catch (e) {
      console.warn("⚠️ Redis cleanup failed:", e.message);
    }

    res.json({
      success: true,
      message: `User ${student_id} deleted from all databases`,
    });
  } catch (error) {
    res.status(500).json({ error: "Delete failed: " + error.message });
  } finally {
    if (mongoClient) await mongoClient.close();
  }
});

// ==================== HEALTH ====================
router.get("/health", async (req, res) => {
  res.json({ status: "healthy", service: "auth-routes", version: "1.0.0" });
});
// ==================== SYNC DATABASES ====================
router.post("/sync-databases", async (req, res) => {
  let mongoClient;
  try {
    const [mysqlUsers] = await pool.query("SELECT student_id FROM users");
    const mysqlIds = new Set(mysqlUsers.map((u) => u.student_id));

    mongoClient = await MongoClient.connect(MONGO_URI);
    const db = mongoClient.db(MONGO_DB);
    const mongoDocs = await db
      .collection("face_embeddings")
      .find({}, { projection: { student_id: 1 } })
      .toArray();
    const mongoIds = mongoDocs.map((d) => d.student_id);
    const orphans = mongoIds.filter((id) => !mysqlIds.has(id));

    for (const id of orphans) {
      await db.collection("face_embeddings").deleteOne({ student_id: id });
      try {
        await cloudinary.uploader.destroy(
          `eduvision/profiles/${id}/${id}_profile`,
        );
      } catch (e) {}
    }

    res.json({
      success: true,
      orphans_deleted: orphans.length,
      orphan_ids: orphans,
    });
  } catch (error) {
    res.status(500).json({ error: "Sync failed: " + error.message });
  } finally {
    if (mongoClient) await mongoClient.close();
  }
});
module.exports = router;
