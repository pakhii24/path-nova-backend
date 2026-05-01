"""
PathNova AI - Career Intelligence Platform
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging

from app.api import resume, analyze, career, interview, chatbot, github
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    logger.info("🚀 PathNova AI Backend starting up...")
    logger.info(f"   API Version: {settings.API_VERSION}")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    yield
    logger.info("🛑 PathNova AI Backend shutting down...")


app = FastAPI(
    title="PathNova AI - Career Intelligence Platform",
    description="""
    ## PathNova AI Backend API

    A production-grade AI-powered career intelligence platform that:
    - 📄 **Parses & analyzes resumes** using NLP
    - 🎯 **ATS scoring** with semantic similarity
    - 🧠 **Skill gap analysis** against job descriptions
    - ✍️ **AI-powered resume rewriting** using Claude
    - 🗺️ **Personalized learning roadmaps**
    - 🎤 **Interview question generation**
    - 💼 **Career path prediction**
    - 🤖 **Real-time resume chatbot**
    - 🐙 **GitHub profile analysis**
    """,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

# CORS - allow the Vite dev server and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount all routers
app.include_router(resume.router,   prefix="/api/v1/resume",   tags=["Resume"])
app.include_router(analyze.router,  prefix="/api/v1/analyze",  tags=["Analysis"])
app.include_router(career.router,   prefix="/api/v1/career",   tags=["Career"])
app.include_router(interview.router,prefix="/api/v1/interview",tags=["Interview"])
app.include_router(chatbot.router,  prefix="/api/v1/chatbot",  tags=["Chatbot"])
app.include_router(github.router,   prefix="/api/v1/github",   tags=["GitHub"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "PathNova AI Career Intelligence Platform",
        "version": settings.API_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.API_VERSION}
