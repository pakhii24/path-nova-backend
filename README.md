# PathNova AI — Career Intelligence Platform

> **An AI-powered resume analysis platform that goes far beyond keyword matching.**
> Built with FastAPI + React + Claude (Anthropic), designed to impress at hackathons and academic evaluations.

---

## 🌟 What Makes This Stand Out

| Feature | Basic Resume Checkers | PathNova AI |
|---|---|---|
| Resume parsing | ✅ Basic text extraction | ✅ Structured NLP extraction (skills, exp, education, projects) |
| ATS scoring | ✅ Simple keyword match | ✅ 5-dimensional AI scoring with semantic similarity |
| Skill gap | ❌ | ✅ Priority-ranked gaps with learning time estimates |
| AI suggestions | ❌ | ✅ Bullet rewrites, action verbs, quantification tips |
| Resume rewriter | ❌ | ✅ Full LLM-powered professional rewrite |
| Learning roadmap | ❌ | ✅ Week-by-week plan with real resources & projects |
| Interview prep | ❌ | ✅ AI question generation + live answer evaluation |
| Career prediction | ❌ | ✅ Role matching with salary, skills, timeline |
| GitHub analysis | ❌ | ✅ Repo quality scoring, language stats, profile insights |
| AI Chatbot | ❌ | ✅ Conversational AI with full resume context |
| Section feedback | ❌ | ✅ Per-section scoring and improvement tips |
| Project suggestions | ❌ | ✅ Portfolio project ideas targeting skill gaps |

---

## 📁 Project Structure

```
path-nova/
├── path-nova-backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── main.py             # FastAPI app + CORS + routers
│   │   ├── core/
│   │   │   └── config.py       # Pydantic settings (env vars)
│   │   ├── models/
│   │   │   └── schemas.py      # All Pydantic request/response models
│   │   ├── services/
│   │   │   ├── resume_parser.py   # PDF/DOCX → structured data
│   │   │   ├── ai_analyzer.py     # Claude API integration (all AI features)
│   │   │   ├── session_store.py   # In-memory session cache
│   │   │   └── github_analyzer.py # GitHub API analysis
│   │   └── api/
│   │       ├── resume.py       # Upload, parse, session management
│   │       ├── analyze.py      # ATS, skill gap, suggestions, full pipeline
│   │       ├── career.py       # Career paths, roadmap, projects
│   │       ├── interview.py    # Question generation + answer evaluation
│   │       ├── chatbot.py      # Conversational AI
│   │       └── github.py       # GitHub profile analysis
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── path-nova-frontend/         # Vite + React frontend
    ├── src/
    │   ├── context/
    │   │   └── SessionContext.jsx  # Global session state (localStorage)
    │   ├── services/
    │   │   └── api.js              # Typed API client for all endpoints
    │   ├── pages/
    │   │   ├── Dashboard.jsx
    │   │   ├── UploadResume.jsx
    │   │   ├── SkillAnalysis.jsx
    │   │   ├── LearningRoadmap.jsx
    │   │   ├── InterviewSimulator.jsx
    │   │   ├── CareerRecommendations.jsx
    │   │   └── Profile.jsx         # + embedded AI chatbot
    │   └── main.jsx
    ├── Dockerfile
    └── nginx.conf
```

---

## ⚡ Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com)

---

### 1. Backend Setup

```bash
cd path-nova-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy NLP model
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Open .env and set:  ANTHROPIC_API_KEY=sk-ant-your-key-here

# Run the server
uvicorn app.main:app --reload --port 8000
```

Backend is now live at **http://localhost:8000**
Interactive API docs at **http://localhost:8000/docs**

---

### 2. Frontend Setup

```bash
cd path-nova-frontend

npm install

# Optional: set backend URL (default is http://localhost:8000/api/v1)
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env

npm run dev
```

Frontend is now live at **http://localhost:5173**

---

### 3. Docker (Full Stack)

```bash
# From the project root
cd path-nova-backend

# Set your API key in .env first
cp .env.example .env && nano .env

docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔌 API Reference

All endpoints are prefixed with `/api/v1`.
Full interactive docs available at `/docs` when server is running.

### Resume

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/resume/upload` | Upload PDF/DOCX → get `session_id` + parsed data |
| `GET`  | `/resume/session/{id}` | Retrieve session data |
| `PUT`  | `/resume/session/{id}/jd` | Update job description for session |

**Upload example:**
```bash
curl -X POST http://localhost:8000/api/v1/resume/upload \
  -F "file=@resume.pdf" \
  -F "job_description=We are looking for a Python backend engineer..." \
  -F "target_role=Senior Backend Engineer"
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "parsed_resume": {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "experience": [...],
    "education": [...],
    "projects": [...]
  },
  "stats": {
    "skills_found": 18,
    "experience_entries": 3,
    "education_entries": 1,
    "projects_found": 4
  }
}
```

---

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze/full` | **Run all analysis modules in parallel** (main endpoint) |
| `POST` | `/analyze/ats-score` | ATS score breakdown |
| `POST` | `/analyze/skill-gap` | Skill gap analysis vs JD |
| `POST` | `/analyze/section-feedback` | Section-wise feedback |
| `POST` | `/analyze/ai-suggestions` | Bullet improvements, keywords, tips |
| `POST` | `/analyze/rewrite-resume` | Full AI resume rewrite |

**Full analysis request:**
```json
{
  "session_id": "your-session-id",
  "job_description": "We need a senior engineer with React, Node.js, AWS...",
  "target_role": "Senior Full Stack Engineer"
}
```

---

### Career

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/career/predict` | Career path predictions + salary + timeline |
| `POST` | `/career/roadmap` | Week-by-week learning roadmap |
| `POST` | `/career/projects` | Portfolio project suggestions |

---

### Interview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/interview/generate` | Generate personalized questions |
| `POST` | `/interview/evaluate-answer` | AI evaluation of a candidate answer |
| `GET`  | `/interview/session/{id}/questions` | Retrieve stored questions |

---

### Chatbot

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chatbot/message` | Send message, get AI response |
| `GET`  | `/chatbot/history/{id}` | Full conversation history |
| `DELETE` | `/chatbot/history/{id}` | Clear chat history |

**Chat request:**
```json
{
  "session_id": "your-session-id",
  "message": "What are my biggest skill gaps for the job description?",
  "history": []
}
```

---

### GitHub

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/github/analyze` | Analyze a GitHub profile URL |

---

## 🧠 AI Architecture

```
User uploads resume
       │
       ▼
┌──────────────────┐
│  Resume Parser   │  pdfplumber + python-docx + regex NLP
│  (services/)     │  → structured ParsedResume dict
└──────┬───────────┘
       │ session stored in memory
       ▼
┌──────────────────────────────────────────────────┐
│              AI Analysis Pipeline                │
│  (async parallel via asyncio.gather)             │
│                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │  ATS Score  │  │  Skill Gap  │  │ Section  │ │
│  │  (Claude)   │  │  (Claude)   │  │ Feedback │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ AI Suggest. │  │   Career    │  │Interview │ │
│  │  (Claude)   │  │  Predict.   │  │Questions │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
│                                                  │
│  Then (uses results from above):                 │
│  ┌───────────────────┐  ┌──────────────────────┐ │
│  │  Learning Roadmap │  │  Project Suggestions │ │
│  └───────────────────┘  └──────────────────────┘ │
└──────────────────────────────────────────────────┘
       │
       ▼
  JSON response → Frontend React dashboard
```

All AI calls use **Claude claude-sonnet-4-20250514** via structured prompts that return validated JSON.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Claude API key |
| `GITHUB_TOKEN` | Optional | Increases GitHub API rate limits |
| `ENVIRONMENT` | Optional | `development` / `production` |
| `MAX_FILE_SIZE_MB` | Optional | Default: `10` |
| `CACHE_TTL` | Optional | Session TTL in seconds. Default: `3600` |

---

## 🚀 Deployment

### Render / Railway / Fly.io (Backend)
```bash
# Set environment variable: ANTHROPIC_API_KEY
# Start command:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Vercel (Frontend)
```bash
cd path-nova-frontend
# Set VITE_API_URL to your deployed backend URL
vercel deploy
```

### Update CORS in production
In `app/core/config.py`, add your frontend domain to `CORS_ORIGINS`.

---

## 📊 Scoring Methodology

### ATS Score (0–100)
- **Skills Match (25%)** — direct skill keyword overlap
- **Experience Relevance (25%)** — semantic similarity of experience to JD
- **Formatting Score (20%)** — structure, section presence, readability
- **Keyword Density (15%)** — JD keywords found in resume
- **Semantic Similarity (15%)** — embedding-level meaning match (via Claude)

### Section Scores (0–100 each)
Each section is scored by Claude on: completeness, impact language, quantification, and relevance.

### GitHub Profile Score (0–100)
Computed from: bio presence, active repos, language diversity, stars, repo descriptions, and topics.

---

## 🧪 Running Tests

```bash
cd path-nova-backend
pytest tests/ -v
```

---

## 📝 Tech Stack

**Backend**
- FastAPI (async REST API)
- Claude claude-sonnet-4-20250514 (all LLM features)
- pdfplumber + PyMuPDF (PDF parsing)
- python-docx (DOCX parsing)
- spaCy en_core_web_sm (NLP)
- httpx (async HTTP)
- Pydantic v2 (validation)

**Frontend**
- React 18 + Vite
- React Router v6
- Tailwind CSS
- Context API (global session state)

**DevOps**
- Docker + Docker Compose
- Nginx (frontend serving + SPA routing)
- uvicorn (ASGI server)

---

## 💡 Key Design Decisions

1. **Session-based architecture** — No database required. Sessions stored in memory with TTL eviction. In production, swap `session_store.py` for Redis.

2. **Parallel AI analysis** — The `/analyze/full` endpoint runs 6 AI calls concurrently via `asyncio.gather`, cutting total analysis time from ~60s to ~15s.

3. **Structured prompts → JSON** — Every Claude call uses explicit JSON schema instructions, making responses directly serializable into Pydantic models.

4. **Progressive enhancement** — The platform works without a job description (general analysis), but quality improves dramatically when one is provided.

5. **Modular routers** — Each feature domain (resume, analyze, career, interview, chatbot, github) is a separate FastAPI router, making the codebase easy to extend.
