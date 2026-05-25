const express = require("express");
const dotenv = require("dotenv");

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5002;

app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
  res.header("Access-Control-Allow-Headers", "Content-Type, Authorization");
  if (req.method === "OPTIONS") return res.sendStatus(200);
  next();
});

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use("/api/attendance", require("./routes/attendance.routes"));

app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    service: "attendance-service",
    version: "1.0.0",
  });
});

app.listen(PORT, () => {
  console.log(`📋 Attendance Service running on port ${PORT}`);
});
