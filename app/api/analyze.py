"""
Analysis API
ATS scoring, skill gap analysis, section feedback, AI suggestions, and full pipeline.
"""

import logging
from fastapi import APIRouter, HTTPException, Body
from typing import Optional

from app.services.ai_analyzer import ai_service
from app.services.session_store import session_store
from app.models.schemas import AnalyzeRequest, ResumeRewriteRequest

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_session_or_404(session_id: str) -> dict:
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if not session.get("parsed_resume"):
        raise HTTPException(status_code=400, detail="No resume found in session. Upload a resume first.")
    return session


@router.post("/ats-score", summary="Compute ATS score against a job description")
async def compute_ats_score(body: AnalyzeRequest):
    """
    Compute a full ATS score breakdown comparing the resume to the job description.
    Returns: overall score, breakdown by category, matched/missing keywords, grade.
    """
    session = _get_session_or_404(body.session_id)

    jd = body.job_description or session.get("job_description", "")
    if not jd:
        raise HTTPException(status_code=400, detail="Job description is required for ATS scoring.")

    # Update session JD if provided
    if body.job_description:
        session_store.update(body.session_id, "job_description", jd)
    if body.target_role:
        session_store.update(body.session_id, "target_role", body.target_role)

    parsed = session["parsed_resume"]
    ats_result = await ai_service.compute_ats_score(parsed, jd)
    session_store.update(body.session_id, "ats_score", ats_result)

    return {"session_id": body.session_id, "ats_score": ats_result}


@router.post("/skill-gap", summary="Analyze skill gaps between resume and JD")
async def analyze_skill_gap(body: AnalyzeRequest):
    """
    Deep skill gap analysis: matching skills, missing skills with priority,
    weak areas, overqualified sections, match percentage.
    """
    session = _get_session_or_404(body.session_id)

    jd = body.job_description or session.get("job_description", "")
    if not jd:
        raise HTTPException(status_code=400, detail="Job description is required for skill gap analysis.")

    if body.job_description:
        session_store.update(body.session_id, "job_description", jd)

    parsed = session["parsed_resume"]
    gap_result = await ai_service.analyze_skill_gap(parsed, jd)
    session_store.update(body.session_id, "skill_gap", gap_result)

    return {"session_id": body.session_id, "skill_gap": gap_result}


@router.post("/section-feedback", summary="Get section-wise resume feedback")
async def section_feedback(body: AnalyzeRequest):
    """
    Score and provide actionable feedback for each resume section:
    Summary, Skills, Experience, Education, Projects.
    """
    session = _get_session_or_404(body.session_id)
    jd = body.job_description or session.get("job_description", "")

    parsed = session["parsed_resume"]
    feedback = await ai_service.generate_section_feedback(parsed, jd)
    session_store.update(body.session_id, "section_feedback", feedback)

    return {"session_id": body.session_id, "section_feedback": feedback}


@router.post("/ai-suggestions", summary="Get AI-powered resume improvement suggestions")
async def ai_suggestions(body: AnalyzeRequest):
    """
    AI suggestions: rewritten summary, improved bullet points,
    action verbs, quantification tips, keyword additions.
    """
    session = _get_session_or_404(body.session_id)
    jd = body.job_description or session.get("job_description", "")

    parsed = session["parsed_resume"]
    suggestions = await ai_service.generate_ai_suggestions(parsed, jd)
    session_store.update(body.session_id, "ai_suggestions", suggestions)

    return {"session_id": body.session_id, "ai_suggestions": suggestions}


@router.post("/rewrite-resume", summary="AI-powered full resume rewrite")
async def rewrite_resume(body: ResumeRewriteRequest):
    """
    Rewrite the entire resume using Claude. Preserves all factual information
    but dramatically improves wording, structure, and impact.
    Returns the rewritten resume as formatted text.
    """
    session = _get_session_or_404(body.session_id)
    parsed = session["parsed_resume"]

    rewritten = await ai_service.rewrite_resume(parsed, body.target_role, body.tone)

    return {
        "session_id": body.session_id,
        "target_role": body.target_role,
        "rewritten_resume": rewritten,
    }


@router.post("/full", summary="Run the complete analysis pipeline")
async def full_analysis(body: AnalyzeRequest):
    """
    Run ALL analysis modules in parallel:
    ATS score + skill gap + section feedback + AI suggestions + 
    learning roadmap + interview questions + career paths + project suggestions.
    
    This is the main endpoint called after resume upload.
    """
    import asyncio

    session = _get_session_or_404(body.session_id)

    jd = body.job_description or session.get("job_description", "")
    target_role = body.target_role or session.get("target_role") or "Software Engineer"

    if body.job_description:
        session_store.update(body.session_id, "job_description", jd)
    if body.target_role:
        session_store.update(body.session_id, "target_role", target_role)

    parsed = session["parsed_resume"]
    current_skills = parsed.get("skills", [])

    # Run analyses that don't depend on others in parallel
    tasks = {}

    if jd:
        tasks["ats"] = ai_service.compute_ats_score(parsed, jd)
        tasks["gap"] = ai_service.analyze_skill_gap(parsed, jd)
    tasks["feedback"] = ai_service.generate_section_feedback(parsed, jd)
    tasks["suggestions"] = ai_service.generate_ai_suggestions(parsed, jd)
    tasks["career"] = ai_service.predict_career_paths(parsed, jd)
    tasks["interview"] = ai_service.generate_interview_questions(parsed, jd, target_role)

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    result_map = dict(zip(tasks.keys(), results))

    # Store results in session
    for key, val in result_map.items():
        if not isinstance(val, Exception):
            field_map = {
                "ats": "ats_score",
                "gap": "skill_gap",
                "feedback": "section_feedback",
                "suggestions": "ai_suggestions",
                "career": "career_paths",
                "interview": "interview_questions",
            }
            session_store.update(body.session_id, field_map[key], val)

    # Dependent tasks: roadmap & projects need missing skills
    gap_data = result_map.get("gap")
    missing_skill_names = []
    if gap_data and not isinstance(gap_data, Exception):
        missing_skill_names = [s.get("skill", "") for s in gap_data.get("missing_skills", [])]

    roadmap, projects = await asyncio.gather(
        ai_service.generate_learning_roadmap(missing_skill_names, target_role, current_skills),
        ai_service.suggest_projects(missing_skill_names, current_skills, target_role),
        return_exceptions=True,
    )

    if not isinstance(roadmap, Exception):
        session_store.update(body.session_id, "learning_roadmap", roadmap)
    if not isinstance(projects, Exception):
        session_store.update(body.session_id, "project_suggestions", projects)

    # Build clean response
    def safe(val):
        return val if not isinstance(val, Exception) else None

    return {
        "session_id": body.session_id,
        "target_role": target_role,
        "parsed_resume": {k: v for k, v in parsed.items() if k != "raw_text"},
        "ats_score": safe(result_map.get("ats")),
        "skill_gap": safe(result_map.get("gap")),
        "section_feedback": safe(result_map.get("feedback")),
        "ai_suggestions": safe(result_map.get("suggestions")),
        "career_paths": safe(result_map.get("career")),
        "interview_questions": safe(result_map.get("interview")),
        "learning_roadmap": safe(roadmap),
        "project_suggestions": safe(projects),
    }
