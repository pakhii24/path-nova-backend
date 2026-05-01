"""
Career API
Career path predictions, learning roadmaps, and project suggestions.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.ai_analyzer import ai_service
from app.services.session_store import session_store

logger = logging.getLogger(__name__)
router = APIRouter()


class RoadmapRequest(BaseModel):
    session_id: str
    target_role: Optional[str] = None
    custom_missing_skills: Optional[List[str]] = None


class CareerRequest(BaseModel):
    session_id: str
    target_role: Optional[str] = None


def _get_session_or_404(session_id: str) -> dict:
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if not session.get("parsed_resume"):
        raise HTTPException(status_code=400, detail="Upload a resume first.")
    return session


@router.post("/predict", summary="Predict career paths for the candidate")
async def predict_career_paths(body: CareerRequest):
    """
    Predict suitable career roles, match percentages, skill gaps per role,
    salary ranges, and a timeline to reach each role.
    """
    session = _get_session_or_404(body.session_id)
    parsed = session["parsed_resume"]
    jd = session.get("job_description", "")
    target_role = body.target_role or session.get("target_role") or "Software Engineer"

    result = await ai_service.predict_career_paths(parsed, jd)
    session_store.update(body.session_id, "career_paths", result)

    return {"session_id": body.session_id, "career_paths": result}


@router.post("/roadmap", summary="Generate a personalized learning roadmap")
async def generate_roadmap(body: RoadmapRequest):
    """
    Create a week-by-week learning roadmap based on the candidate's skill gaps
    and target role. Includes real resources, projects, and time estimates.
    """
    session = _get_session_or_404(body.session_id)
    parsed = session["parsed_resume"]
    current_skills = parsed.get("skills", [])
    target_role = body.target_role or session.get("target_role") or "Software Engineer"

    # Use stored skill gap or custom list
    missing_skills = body.custom_missing_skills
    if not missing_skills:
        gap = session.get("skill_gap")
        if gap:
            missing_skills = [s.get("skill", "") for s in gap.get("missing_skills", [])]
        else:
            missing_skills = []

    if not missing_skills:
        # Fallback: ask Claude to infer from resume vs target role
        missing_skills = ["Docker", "CI/CD", "Cloud Deployment", "System Design"]

    roadmap = await ai_service.generate_learning_roadmap(missing_skills, target_role, current_skills)
    session_store.update(body.session_id, "learning_roadmap", roadmap)

    return {"session_id": body.session_id, "learning_roadmap": roadmap}


@router.post("/projects", summary="Suggest portfolio projects to fill skill gaps")
async def suggest_projects(body: CareerRequest):
    """
    Suggest specific portfolio projects the candidate can build to
    demonstrate missing skills and impress recruiters.
    """
    session = _get_session_or_404(body.session_id)
    parsed = session["parsed_resume"]
    current_skills = parsed.get("skills", [])
    target_role = body.target_role or session.get("target_role") or "Software Engineer"

    gap = session.get("skill_gap") or {}
    missing_skills = [s.get("skill", "") for s in gap.get("missing_skills", [])]
    if not missing_skills:
        missing_skills = ["Docker", "Cloud", "System Design"]

    projects = await ai_service.suggest_projects(missing_skills, current_skills, target_role)
    session_store.update(body.session_id, "project_suggestions", projects)

    return {"session_id": body.session_id, "project_suggestions": projects}


@router.get("/session/{session_id}/career-data", summary="Get all stored career analysis")
async def get_career_data(session_id: str):
    """Return all previously computed career data for a session (no recompute)."""
    session = _get_session_or_404(session_id)
    return {
        "session_id": session_id,
        "career_paths": session.get("career_paths"),
        "learning_roadmap": session.get("learning_roadmap"),
        "project_suggestions": session.get("project_suggestions"),
    }
