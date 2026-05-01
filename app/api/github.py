"""
GitHub Profile Analyzer API
"""

import logging
from fastapi import APIRouter, HTTPException
from app.services.github_analyzer import github_analyzer
from app.services.session_store import session_store
from app.models.schemas import GitHubAnalyzeRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", summary="Analyze a GitHub profile")
async def analyze_github(body: GitHubAnalyzeRequest):
    """
    Analyze a GitHub profile:
    - Repository quality scoring
    - Language distribution
    - Profile completeness score
    - Strengths and improvement suggestions
    - Skills demonstrated through code
    """
    try:
        result = await github_analyzer.analyze(body.github_url)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("GitHub analysis error")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch GitHub data. Check the URL and try again. ({e})",
        )

    # Store in session if session_id provided
    if body.session_id and session_store.session_exists(body.session_id):
        session_store.update(body.session_id, "github_analysis", result)

    return {"github_analysis": result}


@router.get("/session/{session_id}", summary="Get stored GitHub analysis")
async def get_github_analysis(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    analysis = session.get("github_analysis")
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="No GitHub analysis found. Call /analyze first.",
        )

    return {"session_id": session_id, "github_analysis": analysis}
