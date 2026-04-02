# 🔷 DevInsight — Code Quality Intelligence Platform

AI-powered platform that analyzes software repositories for bugs, technical debt, code smells, and security vulnerabilities.

## ✨ Features

- **🔍 Code Analysis** — Static analysis with cyclomatic complexity, technical debt estimation, risk classification
- **🐞 Bug Detection** — AST-based detection for Python/JS with auto-fix generation
- **🤖 AI Insights** — Heuristic analysis with suggestions, refactoring strategies, security alerts
- **💬 Bug Chatbot** — Each bug gets its own AI chatbot for explanations and guidance
- **📊 Visual Dashboard** — Recharts-powered charts: risk distribution, complexity trends, hotspots
- **📄 Reports** — Download PDF, DOCX, or JSON reports
- **⏱️ Continuous Monitoring** — Celery Beat re-analyzes repos every 24 hours
- **🔐 Auth** — Google OAuth via Supabase with JWT middleware
- **📜 History** — Timeline view with version comparison and trend tracking

## 🏗️ Architecture

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python) |
| **Frontend** | React + Vite |
| **Database & Auth** | Supabase (PostgreSQL + Auth) |
| **Task Queue** | Celery + Redis |
| **AI Engine** | Rule-based heuristic (LLM-ready) |

## 🗂️ Project Structure

```
dev_insight/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── config.py            # Settings
│   │   ├── middleware/          # JWT auth
│   │   ├── routers/             # 7 API route modules
│   │   ├── services/            # 6 business logic modules
│   │   ├── models/              # Pydantic schemas
│   │   └── tasks/               # Celery tasks
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # 8 page components
│   │   ├── components/          # Layout, shared UI
│   │   ├── services/            # API client, Supabase
│   │   └── contexts/            # Auth context
│   ├── package.json
│   └── vite.config.js
├── database/
│   └── schema.sql               # Supabase SQL schema
├── docker-compose.yml
└── .env
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account (cloud)
- Redis (cloud or local)

### 1. Database Setup

1. Go to your [Supabase dashboard](https://supabase.com/dashboard)
2. Open the **SQL Editor**
3. Paste and run the contents of `database/schema.sql`
4. Under **Authentication → Providers**, enable **Google OAuth**
   - Set the Google Client ID and Secret
   - Add `http://localhost:5173/auth/callback` as a redirect URL

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000/api/docs` (Swagger UI).

### 3. Celery Worker (for async analysis)

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

### 5. Docker (Alternative)

```bash
docker-compose up --build
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/auth/login` | Get Google OAuth URL |
| `POST` | `/api/auth/callback` | Exchange token |
| `GET` | `/api/auth/me` | Get current user |
| `POST` | `/api/repositories/submit` | Submit GitHub repo |
| `POST` | `/api/repositories/snippet` | Submit code snippet |
| `GET` | `/api/analysis/dashboard` | Dashboard stats |
| `GET` | `/api/analysis/{id}` | Analysis result |
| `GET` | `/api/bugs/analysis/{id}` | Bugs by analysis |
| `POST` | `/api/chat/bug/{id}` | Chat about a bug |
| `POST` | `/api/reports/generate` | Generate report |
| `GET` | `/api/insights/analysis/{id}` | AI insights |

## 🔧 Environment Variables

See `.env` file for all required configuration including:
- Google OAuth credentials
- GitHub token
- Supabase URL & keys
- Redis connection URL

## 📊 Supported Languages

| Language | Static Analysis | Bug Detection |
|---|---|---|
| Python | ✅ Full (AST) | ✅ Full (AST + rules) |
| JavaScript/TypeScript | ✅ Full (regex) | ✅ Full (rules) |
| Java | ✅ Basic | ✅ Basic |
| C/C++ | ✅ Basic | ✅ Basic |

## 📝 License

MIT
