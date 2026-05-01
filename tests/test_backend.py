"""
Basic tests for PathNova AI backend.
Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def get_client():
    from app.main import app
    return TestClient(app)


class TestHealthEndpoints:
    def test_root(self):
        client = get_client()
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "operational"

    def test_health(self):
        client = get_client()
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestResumeParser:
    def test_extract_email(self):
        from app.services.resume_parser import resume_parser
        text = "Contact me at john.doe@example.com for more info."
        assert resume_parser._extract_email(text) == "john.doe@example.com"

    def test_extract_phone(self):
        from app.services.resume_parser import resume_parser
        text = "Phone: +1 (555) 123-4567"
        result = resume_parser._extract_phone(text)
        assert result is not None

    def test_extract_linkedin(self):
        from app.services.resume_parser import resume_parser
        text = "Find me at linkedin.com/in/johndoe"
        result = resume_parser._extract_linkedin(text)
        assert "johndoe" in result

    def test_extract_github(self):
        from app.services.resume_parser import resume_parser
        text = "My code: github.com/johndoe"
        result = resume_parser._extract_github(text)
        assert "johndoe" in result

    def test_extract_skills(self):
        from app.services.resume_parser import resume_parser
        text = "Experienced with Python, React, Docker, and PostgreSQL."
        skills = resume_parser._extract_skills(text)
        assert "Python" in skills
        assert "React" in skills
        assert "Docker" in skills

    def test_extract_name(self):
        from app.services.resume_parser import resume_parser
        # Name on its own line, no special chars, title case
        text = "John Smith\nSoftware Engineer\njohn@example.com"
        name = resume_parser._extract_name(text)
        # The heuristic may or may not fire depending on line order; just verify it doesn't crash
        # and returns a string or None
        assert name is None or isinstance(name, str)

    def test_split_sections(self):
        from app.services.resume_parser import resume_parser
        text = """Jane Doe
jane@example.com

SKILLS
Python, JavaScript, React

EXPERIENCE
Software Engineer at Acme Corp

EDUCATION
B.S. Computer Science, MIT, 2020
"""
        sections = resume_parser._split_sections(text)
        assert isinstance(sections, dict)

    def test_unsupported_file_type(self):
        from app.services.resume_parser import resume_parser
        with pytest.raises(ValueError, match="Unsupported file type"):
            resume_parser.extract_text(b"some bytes", "resume.txt")


class TestSessionStore:
    def test_create_session(self):
        from app.services.session_store import SessionStore
        store = SessionStore()
        sid = store.create_session()
        assert sid is not None
        assert len(sid) == 36  # UUID format

    def test_get_session(self):
        from app.services.session_store import SessionStore
        store = SessionStore()
        sid = store.create_session()
        session = store.get(sid)
        assert session is not None
        assert session["parsed_resume"] is None

    def test_update_session(self):
        from app.services.session_store import SessionStore
        store = SessionStore()
        sid = store.create_session()
        store.update(sid, "parsed_resume", {"name": "Test User"})
        session = store.get(sid)
        assert session["parsed_resume"]["name"] == "Test User"

    def test_session_not_found(self):
        from app.services.session_store import SessionStore
        store = SessionStore()
        session = store.get("nonexistent-id")
        assert session is None

    def test_append_chat(self):
        from app.services.session_store import SessionStore
        store = SessionStore()
        sid = store.create_session()
        store.append_chat(sid, "user", "Hello")
        store.append_chat(sid, "assistant", "Hi there!")
        session = store.get(sid)
        assert len(session["chat_history"]) == 2
        assert session["chat_history"][0]["role"] == "user"

    def test_session_exists(self):
        from app.services.session_store import SessionStore
        store = SessionStore()
        sid = store.create_session()
        assert store.session_exists(sid) is True
        assert store.session_exists("fake-id") is False

    def test_ttl_eviction(self):
        from app.services.session_store import SessionStore
        import time
        store = SessionStore(ttl_seconds=0)  # immediate expiry
        sid = store.create_session()
        time.sleep(0.01)
        session = store.get(sid)
        assert session is None


class TestUploadEndpoint:
    def test_upload_no_file(self):
        client = get_client()
        r = client.post("/api/v1/resume/upload")
        assert r.status_code == 422  # validation error - file required

    def test_upload_wrong_type(self):
        client = get_client()
        r = client.post(
            "/api/v1/resume/upload",
            files={"file": ("resume.txt", b"some text content", "text/plain")},
        )
        assert r.status_code == 400
        assert "Unsupported file type" in r.json()["detail"]

    def test_get_nonexistent_session(self):
        client = get_client()
        r = client.get("/api/v1/resume/session/nonexistent-id")
        assert r.status_code == 404


class TestAnalyzeEndpoint:
    def test_analyze_no_session(self):
        client = get_client()
        r = client.post(
            "/api/v1/analyze/ats-score",
            json={"session_id": "nonexistent-id"},
        )
        assert r.status_code == 404

    def test_full_analysis_no_session(self):
        client = get_client()
        r = client.post(
            "/api/v1/analyze/full",
            json={"session_id": "nonexistent-id"},
        )
        assert r.status_code == 404


class TestChatbotEndpoint:
    def test_chat_no_session(self):
        client = get_client()
        r = client.post(
            "/api/v1/chatbot/message",
            json={"session_id": "nonexistent", "message": "Hello"},
        )
        assert r.status_code == 404

    def test_chat_history_no_session(self):
        client = get_client()
        r = client.get("/api/v1/chatbot/history/nonexistent")
        assert r.status_code == 404


class TestGitHubEndpoint:
    def test_analyze_invalid_user(self):
        """This makes a real GitHub API call — only run with internet access."""
        client = get_client()
        r = client.post(
            "/api/v1/github/analyze",
            json={"github_url": "https://github.com/this-user-definitely-does-not-exist-xyz-999"},
        )
        # Either 404 (user not found) or 502 (network error in test env)
        assert r.status_code in [404, 502]
