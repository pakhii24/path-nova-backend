"""
Resume Upload & Parsing API
Handles file upload, text extraction, and session creation.
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional

from app.services.resume_parser import resume_parser
from app.services.session_store import session_store
from app.models.schemas import ParsedResume
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


@router.post("/upload", summary="Upload and parse a resume file")
async def upload_resume(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    target_role: Optional[str] = Form(None),
):
    """
    Upload a PDF or DOCX resume. Returns a session_id and parsed resume data.
    The session_id is used for all subsequent analysis calls.
    """
    # Validate file type
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Please upload PDF or DOCX.",
        )

    # Read file bytes
    file_bytes = await file.read()

    # Enforce size limit
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB.",
        )

    # Parse resume
    try:
        parsed = resume_parser.parse(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error parsing resume")
        raise HTTPException(status_code=500, detail="Failed to parse resume. Please try again.")

    # Create session and store parsed resume
    session_id = session_store.create_session()
    session_store.update(session_id, "parsed_resume", parsed)

    if job_description:
        session_store.update(session_id, "job_description", job_description)
    if target_role:
        session_store.update(session_id, "target_role", target_role)

    return JSONResponse({
        "session_id": session_id,
        "message": "Resume parsed successfully",
        "parsed_resume": {
            k: v for k, v in parsed.items() if k != "raw_text"
        },
        "stats": {
            "skills_found": len(parsed.get("skills", [])),
            "experience_entries": len(parsed.get("experience", [])),
            "education_entries": len(parsed.get("education", [])),
            "projects_found": len(parsed.get("projects", [])),
            "name_detected": parsed.get("name"),
            "email_detected": bool(parsed.get("email")),
        },
    })


@router.get("/session/{session_id}", summary="Get session data")
async def get_session(session_id: str):
    """Retrieve all stored data for a session."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    return {
        "session_id": session_id,
        "has_resume": session["parsed_resume"] is not None,
        "has_jd": session["job_description"] is not None,
        "target_role": session["target_role"],
        "parsed_resume": {
            k: v for k, v in (session["parsed_resume"] or {}).items()
            if k != "raw_text"
        } if session["parsed_resume"] else None,
    }


@router.put("/session/{session_id}/jd", summary="Update job description for a session")
async def update_job_description(
    session_id: str,
    job_description: str = Form(...),
    target_role: Optional[str] = Form(None),
):
    """Update or set the job description for an existing session."""
    if not session_store.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    session_store.update(session_id, "job_description", job_description)
    if target_role:
        session_store.update(session_id, "target_role", target_role)

    return {"message": "Job description updated", "session_id": session_id}
