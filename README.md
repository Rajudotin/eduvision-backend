# EduVision - Backend

AI-Powered Face Recognition Attendance System

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal.svg)](https://fastapi.tiangolo.com/)
[![Express](https://img.shields.io/badge/Express-4.18-lightgrey.svg)](https://expressjs.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0-green.svg)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Deployed](https://img.shields.io/badge/Deployed-Railway-purple.svg)](https://railway.app/)

---

## 📖 Table of Contents

- Architecture
- Tech Stack
- Services
- API Gateway & Routing
- API Endpoints
- Database Design (Polyglot Persistence)
- Quick Start
- Environment Variables
- Deployment
- Contributing
- License

---

## 🏗 Architecture

```text
                           ┌────────────────────────────────┐
                           │        API GATEWAY (Nginx)     │
                           │ Load Balancer | Rate Limiter   │
                           └───────────────┬────────────────┘
                                           │
      ┌────────────────────────────────────┼─────────────────────────────────────┐
      ▼                                    ▼                                     ▼
┌─────────────┐                    ┌───────────────┐                     ┌───────────────┐
│ Auth Service│ (Node:5001)       │ Attendance     │ (Node:5002)        │ Report Service│ (Node:5003)
└──────┬──────┘                    └───────┬───────┘                     └───────┬───────┘
       │                                   │                                          │
       ▼                                   ▼                                          ▼
  ┌─────────────┐                 ┌─────────────┐                            ┌─────────────┐
  │ WhatsApp     │ (Node:5004)     │ Face Recognition│ (Python:8000)         │ Datastores  │
  └─────────────┘                 │ FastAPI + InsightFace + OpenCV     │ MySQL/Mongo/Redis
                                  └────────────────┘                            │ Cloudinary
```

---

## 🛠 Tech Stack

| Layer              | Technology                                | Purpose                                        |
| ------------------ | ----------------------------------------- | ---------------------------------------------- |
| AI / ML            | Python 3.10, FastAPI, InsightFace, OpenCV | Face detection + embedding + recognition       |
| Business Logic     | Node.js, Express.js                       | REST APIs for auth/attendance/reports/whatsapp |
| API Gateway        | Nginx                                     | Reverse proxy, CORS, rate limiting             |
| Relational DB      | MySQL                                     | Users + attendance + reports (metadata)        |
| Vector/Document DB | MongoDB (Atlas)                           | Face embeddings storage                        |
| Cache              | Redis                                     | Sessions, rate limiting, token blacklisting    |
| File Storage/CDN   | Cloudinary                                | Profile images & uploads                       |
| Authentication     | JWT + bcrypt                              | Secure login & role-based access               |
| Messaging          | Twilio / WhatsApp Cloud API               | Absence and monthly attendance notifications   |
| Deployment         | Railway + Docker                          | Containerized services                         |

---

## 📦 Services

### 🔐 Auth Service (Node.js - port 5001)

- User registration & login
- JWT token generation
- Role support (Student/Teacher/Admin)
- Session caching with Redis

**Gateway routes (via Nginx):**

- `/api/auth/*`

### 📋 Attendance Service (Node.js - port 5002)

- Attendance marking from photo
- Manual verification
- Today’s attendance + student history

**Gateway routes (via Nginx):**

- `/api/attendance/*`

### 📊 Report Service (Node.js - port 5003)

- PDF report generation
- Excel report generation
- Attendance analytics

**Gateway routes (via Nginx):**

- `/api/reports/*`

### 💬 WhatsApp Service (Node.js - port 5004)

- Send absence alerts
- Send monthly attendance reports
- Webhook handling for message replies

**Gateway routes (via Nginx):**

- `/api/whatsapp/*`

### 🤖 Face Recognition Service (Python - port 8000)

- Detect faces and generate embeddings
- Match embeddings using cosine similarity/confidence tiers
- Provide recognition and registration endpoints

**Gateway routes (via Nginx):**

- `/api/face/*`
- `/api/register/*`
- `/api/recognize/*`

> Face API is implemented in `backend/ai_services/` using FastAPI.

---

## 📡 API Gateway & Routing (Nginx)

Nginx runs on **port 80** and proxies requests to each microservice.

Common gateway features:

- CORS enabled (wildcard origin)
- `client_max_body_size 50M`
- Rate limiting (configured in `docker/nginx/eduvision.conf`)

Health endpoints (gateway):

- `GET /health/face`
- `GET /health/auth`
- `GET /health/attendance`
- `GET /health/report`
- `GET /health/whatsapp`
- `GET /gateway-status`

---

## 🧾 API Endpoints (Gateway)

> Note: Actual request/response shapes depend on each service implementation.
> Routes below match the gateway mappings in `docker/nginx/eduvision.conf`.

### Authentication

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`

### Attendance

- `POST /api/attendance/mark`
- `POST /api/attendance/manual-mark`
- `GET /api/attendance/today`
- `GET /api/attendance/student/:id`

### Face Recognition

- `POST /api/face/…`
- `POST /api/register/…`
- `POST /api/recognize/…`

### Reports

- `GET /api/reports/summary/:id`
- `GET /api/reports/pdf/:id`
- `GET /api/reports/excel/:id`

### WhatsApp

- `POST /api/whatsapp/send-absence-alerts`
- `POST /api/whatsapp/send-monthly-report/:id`
- `POST /api/whatsapp/webhook`

---

## 🗄 Database Design (Polyglot Persistence)

| Database   | Stores                                      | Why                                      |
| ---------- | ------------------------------------------- | ---------------------------------------- |
| MySQL      | Users, attendance records                   | ACID + JOINs                             |
| MongoDB    | Face embeddings (512-dim / model-dependent) | Flexible document storage for embeddings |
| Redis      | Sessions, cache, rate limiting              | Fast access and token blacklisting       |
| Cloudinary | Images & uploads                            | CDN delivery, easy storage handling      |

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- MySQL 8.0
- MongoDB 6.0 (Atlas recommended)
- Redis 7.0
- Nginx

### Installation

Clone repository:

```bash
git clone https://github.com/Rajudotin/eduvision-backend.git
cd eduvision-backend
```

### Start all services (Windows)

This project includes a one-click script:

```powershell
. 1start_all.ps1 1
```

What it starts (from `start_all.ps1`):

1. Redis
2. Face Recognition service (uvicorn on port 8000)
3. Auth service (npm dev)
4. Attendance service (npm dev)
5. Report service (npm dev)
6. WhatsApp service (npm dev)
7. Nginx gateway

### Start services individually

**Auth service**

```bash
cd backend/auth_service
npm install
npm run dev
```

**Attendance service**

```bash
cd backend/attendance_service
npm install
npm run dev
```

**Report service**

```bash
cd backend/report_service
npm install
npm run dev
```

**WhatsApp service**

```bash
cd backend/whatsapp_service
npm install
npm run dev
```

**Face Recognition service**

```bash
cd backend/ai_services
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🔐 Environment Variables

This backend expects environment variables for each service.

Common variables (examples):

### Server / Node settings

- `NODE_ENV` (production/development)

### MySQL (Aiven / or any MySQL host)

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

### MongoDB Atlas

- `MONGODB_URI`
- `MONGODB_DB`

### Redis (Upstash / or self-hosted)

- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`

### JWT

- `JWT_SECRET`
- `JWT_EXPIRE` (e.g., `7d`)

### Cloudinary

- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### WhatsApp / Twilio

- `WHATSAPP_PHONE_ID`
- `WHATSAPP_TOKEN`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`

> Ensure you set these values before starting any microservice.

---

## 🚢 Deployment

### Railway (Recommended)

The repo includes `backend/railway.json` with build and start commands per microservice.

- Push to GitHub
- Connect the repository to Railway
- Configure environment variables in Railway
- Deploy

### Docker

A full Docker-based setup exists under `docker/`.
Typical workflow:

- configure env vars
- run docker compose

---

## 📂 Project Structure

```text
backend/
├── auth_service/           # Authentication microservice
│   ├── src/
│   └── package.json
├── attendance_service/     # Attendance microservice
│   ├── src/
│   └── package.json
├── report_service/         # Report generation microservice
│   ├── src/
│   └── package.json
├── whatsapp_service/       # WhatsApp notification microservice
│   ├── src/
│   └── package.json
├── ai_services/            # Face recognition (Python/FastAPI)
│   ├── app/
│   └── requirements.txt
├── docker/
│   └── nginx/
│       ├── eduvision.conf # Nginx gateway routing
│       └── nginx.conf
└── start_all.ps1          # One-click start script (Windows)
```

---

## 🤝 Contributing

- Fork the repository
- Create a feature branch: `git checkout -b feature/amazing-feature`
- Commit changes: `git commit -m "Add amazing feature"`
- Push: `git push origin feature/amazing-feature`
- Open a Pull Request

---

## 📄 License

MIT License

---

## 📞 Contact

- **Balavenkata Raju**
- **Email:** balavenkatarajusingampalli@gmail.com

---

<p align="center">Made with  by Raju | Acharya Nagarjuna University</p>
