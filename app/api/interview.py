"""
Interview Simulator API
Generate, evaluate, and manage interview questions.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.ai_analyzer import ai_service
from app.services.session_store import session_store
import httpx

logger = logging.getLogger(__name__)
router = APIRouter()

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"


class InterviewRequest(BaseModel):
    session_id: str
    target_role: Optional[str] = None
    job_description: Optional[str] = None
    categories: Optional[List[str]] = None  # filter by category


class EvaluateAnswerRequest(BaseModel):
    session_id: str
    question_id: int
    question: str
    user_answer: str
    skill_tested: str
    expected_points: List[str]


def _get_session_or_404(session_id: str) -> dict:
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if not session.get("parsed_resume"):
        raise HTTPException(status_code=400, detail="Upload a resume first.")
    return session


@router.post("/generate", summary="Generate interview questions for the candidate")
async def generate_questions(body: InterviewRequest):
    """
    Generate personalized interview questions (technical, behavioral, HR, situational)
    based on the candidate's resume and target role.
    """
    session = _get_session_or_404(body.session_id)
    parsed = session["parsed_resume"]
    jd = body.job_description or session.get("job_description", "")
    target_role = body.target_role or session.get("target_role") or "Software Engineer"

    result = await ai_service.generate_interview_questions(parsed, jd, target_role)

    # Filter by categories if requested
    if body.categories:
        cats = [c.lower() for c in body.categories]
        result["questions"] = [
            q for q in result["questions"]
            if q.get("category", "").lower() in cats
        ]
        result["total"] = len(result["questions"])

    session_store.update(body.session_id, "interview_questions", result)
    return {"session_id": body.session_id, "interview_questions": result}


@router.post("/evaluate-answer", summary="Evaluate a candidate's interview answer")
async def evaluate_answer(body: EvaluateAnswerRequest):
    """
    Use AI to evaluate a candidate's answer to an interview question.
    Returns a score, feedback, and model answer.
    """
    from app.core.config import settings

    system = (
        "You are a senior technical interviewer. Evaluate candidate interview answers "
        "objectively and provide constructive feedback. Return ONLY valid JSON."
    )
    user = f"""
Evaluate this interview answer:

QUESTION: {body.question}
SKILL TESTED: {body.skill_tested}
EXPECTED KEY POINTS: {body.expected_points}
CANDIDATE ANSWER: {body.user_answer}

Return ONLY this JSON:
{{
  "score": <0-100>,
  "grade": "Excellent|Good|Fair|Needs Improvement",
  "strengths": ["what the candidate did well"],
  "gaps": ["what was missing or incorrect"],
  "model_answer": "ideal 3-4 sentence answer",
  "feedback": "personalized 2-3 sentence coaching feedback"
}}
"""
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "max_tokens": 800,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    import json, re
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GROQ_URL, headers=headers, json=payload)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]

    raw = re.sub(r"```(?:json)?\n?", "", raw).strip().rstrip("```").strip()
    start = raw.find("{"); end = raw.rfind("}") + 1
    if start != -1: raw = raw[start:end]
    evaluation = json.loads(raw)

    return {
        "session_id": body.session_id,
        "question_id": body.question_id,
        "evaluation": evaluation,
    }


@router.get("/session/{session_id}/questions", summary="Get stored interview questions")
async def get_questions(session_id: str, category: Optional[str] = None):
    """Return previously generated interview questions for a session."""
    session = _get_session_or_404(session_id)
    questions_data = session.get("interview_questions")

    if not questions_data:
        raise HTTPException(
            status_code=404,
            detail="No interview questions generated yet. Call /generate first.",
        )

    if category:
        questions_data["questions"] = [
            q for q in questions_data["questions"]
            if q.get("category", "").lower() == category.lower()
        ]

    return {"session_id": session_id, "interview_questions": questions_data}
