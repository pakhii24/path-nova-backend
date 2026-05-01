"""
Resume Chatbot API
Real-time conversational AI that answers questions about the user's resume.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.services.ai_analyzer import ai_service
from app.services.session_store import session_store
from app.models.schemas import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/message", summary="Chat with AI about your resume")
async def chat(body: ChatRequest):
    """
    Send a message to the resume chatbot. The AI has full context of:
    - The parsed resume
    - The job description (if provided)
    - The conversation history
    
    Example questions:
    - "What are my strongest skills?"
    - "How can I improve my ATS score?"
    - "What jobs am I best suited for?"
    - "Rewrite my summary for a senior role"
    """
    session = session_store.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if not session.get("parsed_resume"):
        raise HTTPException(status_code=400, detail="Upload a resume first to use the chatbot.")

    parsed = session["parsed_resume"]
    jd = session.get("job_description", "")

    # Use provided history or fall back to stored chat history
    history = body.history or session.get("chat_history", [])

    result = await ai_service.resume_chat(
        message=body.message,
        resume_context=parsed,
        history=history,
        job_description=jd,
    )

    # Persist conversation to session
    session_store.append_chat(body.session_id, "user", body.message)
    session_store.append_chat(body.session_id, "assistant", result["response"])

    return {
        "session_id": body.session_id,
        "response": result["response"],
        "suggestions": result["suggestions"],
    }


@router.get("/history/{session_id}", summary="Get chat history for a session")
async def get_history(session_id: str):
    """Retrieve the full conversation history for a session."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    return {
        "session_id": session_id,
        "history": session.get("chat_history", []),
        "message_count": len(session.get("chat_history", [])),
    }


@router.delete("/history/{session_id}", summary="Clear chat history")
async def clear_history(session_id: str):
    """Clear the chat history for a session (start fresh conversation)."""
    if not session_store.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    session_store.update(session_id, "chat_history", [])
    return {"message": "Chat history cleared", "session_id": session_id}
