"""
AI Analysis Service
Powered by Groq (free tier) + Llama 3.3 70B.
Groq is ideal for demos: free, extremely fast (1-3s responses), high quality.
Sign up at https://console.groq.com to get a free API key.
"""

import json
import logging
import re
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"


class AIAnalysisService:

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        }

    async def _call_groq(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        payload = {
            "model": MODEL,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(GROQ_API_URL, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    def _parse_json(self, text: str) -> dict:
        text = re.sub(r"```(?:json)?\n?", "", text).strip().rstrip("```").strip()
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]
        return json.loads(text)

    def _parse_json_array(self, text: str) -> list:
        text = re.sub(r"```(?:json)?\n?", "", text).strip().rstrip("```").strip()
        start = text.find("[")
        end   = text.rfind("]") + 1
        if start != -1 and end > start:
            text = text[start:end]
        return json.loads(text)

    async def compute_ats_score(self, parsed_resume: dict, job_description: str) -> dict:
        system = "You are an ATS scoring engine. Return ONLY valid JSON, no explanation text outside the JSON."
        user = f"""Analyze this resume against the job description.

RESUME SKILLS: {', '.join(parsed_resume.get('skills', []))}
EXPERIENCE: {json.dumps([e.get('title','') + ' at ' + e.get('company','') for e in parsed_resume.get('experience', [])[:3]])}
RESUME TEXT: {parsed_resume.get('raw_text', '')[:1500]}
JOB DESCRIPTION: {job_description[:2000]}

Return ONLY this JSON:
{{
  "overall_score": <0-100>,
  "breakdown": {{"skills_match": <0-100>, "experience_relevance": <0-100>, "formatting_score": <0-100>, "keyword_density": <0-100>, "semantic_similarity": <0-100>}},
  "matched_keywords": ["keyword1"],
  "missing_keywords": ["keyword1"],
  "grade": "<A+|A|B+|B|C|D>",
  "summary": "<2-3 sentence analysis>"
}}"""
        return self._parse_json(await self._call_groq(system, user, 1200))

    async def analyze_skill_gap(self, parsed_resume: dict, job_description: str) -> dict:
        system = "You are a career skills expert. Return ONLY valid JSON."
        user = f"""Compare candidate skills against job requirements.

CANDIDATE SKILLS: {', '.join(parsed_resume.get('skills', []))}
RESUME TEXT: {parsed_resume.get('raw_text', '')[:1000]}
JOB DESCRIPTION: {job_description[:2000]}

Return ONLY this JSON:
{{
  "matching_skills": ["skill1"],
  "missing_skills": [{{"skill": "name", "importance": "critical", "current_level": null, "required_level": "intermediate", "learning_time_weeks": 4}}],
  "weak_skills": ["skill"],
  "overqualified_areas": ["area"],
  "match_percentage": <0-100>,
  "strengths": ["strength1"],
  "weaknesses": ["weakness1"]
}}"""
        return self._parse_json(await self._call_groq(system, user, 1800))

    async def generate_section_feedback(self, parsed_resume: dict, job_description: str = "") -> dict:
        system = "You are a professional resume reviewer. Return ONLY valid JSON."
        user = f"""Review this resume section by section.

NAME: {parsed_resume.get('name')}
SUMMARY: {parsed_resume.get('summary', 'None')}
SKILLS COUNT: {len(parsed_resume.get('skills', []))}
EXPERIENCE COUNT: {len(parsed_resume.get('experience', []))} roles
PROJECTS COUNT: {len(parsed_resume.get('projects', []))}
{"JD: " + job_description[:600] if job_description else ""}

Return ONLY this JSON:
{{
  "sections": [
    {{"section": "Summary", "score": <0-100>, "feedback": "...", "suggestions": ["tip1", "tip2"]}},
    {{"section": "Skills", "score": <0-100>, "feedback": "...", "suggestions": ["tip1"]}},
    {{"section": "Experience", "score": <0-100>, "feedback": "...", "suggestions": ["tip1"]}},
    {{"section": "Education", "score": <0-100>, "feedback": "...", "suggestions": ["tip1"]}},
    {{"section": "Projects", "score": <0-100>, "feedback": "...", "suggestions": ["tip1"]}}
  ],
  "overall_impression": "2-3 sentence review",
  "top_improvements": ["improvement1", "improvement2", "improvement3"]
}}"""
        return self._parse_json(await self._call_groq(system, user, 2000))

    async def generate_ai_suggestions(self, parsed_resume: dict, job_description: str = "") -> dict:
        system = "You are an expert resume writer. Return ONLY valid JSON."
        bullets = []
        for exp in parsed_resume.get("experience", [])[:3]:
            bullets.extend(exp.get("description", [])[:2])
        user = f"""Generate resume improvements.

SUMMARY: {parsed_resume.get('summary', 'No summary')}
BULLETS: {json.dumps(bullets[:5])}
SKILLS: {', '.join(parsed_resume.get('skills', [])[:15])}
{"JD: " + job_description[:600] if job_description else ""}

Return ONLY this JSON:
{{
  "summary_rewrite": "improved summary 3-4 sentences",
  "bullet_improvements": [{{"original": "old bullet", "improved": "new bullet with metrics", "reason": "why better"}}],
  "action_verb_suggestions": ["Led", "Architected", "Engineered", "Optimized", "Delivered"],
  "quantification_tips": ["Add percentages to improvements", "Include team sizes"],
  "formatting_tips": ["Use consistent date format"],
  "keywords_to_add": ["keyword1", "keyword2", "keyword3"]
}}"""
        return self._parse_json(await self._call_groq(system, user, 2500))

    async def generate_learning_roadmap(self, missing_skills: list, target_role: str, current_skills: list) -> dict:
        system = "You are a technical mentor. Return ONLY valid JSON."
        weeks = min(max(len(missing_skills) * 2, 4), 8)
        user = f"""Create a {weeks}-week learning roadmap.

TARGET ROLE: {target_role}
CURRENT SKILLS: {', '.join(current_skills[:15])}
MISSING SKILLS: {json.dumps(missing_skills[:8])}

Return ONLY this JSON:
{{
  "total_weeks": {weeks},
  "target_role": "{target_role}",
  "weeks": [
    {{
      "week": 1,
      "title": "week title",
      "skill": "primary skill",
      "topics": ["topic1", "topic2"],
      "projects": ["project to build"],
      "resources": [{{"title": "resource", "type": "course", "url": null, "platform": "YouTube", "duration": "3 hours", "free": true}}],
      "estimated_hours": 10
    }}
  ],
  "milestones": ["milestone1", "milestone2"],
  "priority_skills": ["skill1", "skill2"]
}}"""
        return self._parse_json(await self._call_groq(system, user, 3500))

    async def generate_interview_questions(self, parsed_resume: dict, job_description: str, target_role: str) -> dict:
        system = "You are an expert technical interviewer. Return ONLY valid JSON."
        user = f"""Generate 10 interview questions.

SKILLS: {', '.join(parsed_resume.get('skills', [])[:15])}
TARGET ROLE: {target_role}
JD: {job_description[:1200]}

Return ONLY this JSON with exactly 10 questions:
{{
  "questions": [
    {{
      "id": 1,
      "question": "question text",
      "category": "technical",
      "difficulty": "medium",
      "skill_tested": "skill name",
      "expected_answer_points": ["point1", "point2"],
      "follow_up": "follow up question"
    }}
  ],
  "total": 10,
  "role_targeted": "{target_role}",
  "focus_areas": ["area1", "area2"]
}}

Mix: 4 technical, 3 behavioral, 2 hr, 1 situational."""
        return self._parse_json(await self._call_groq(system, user, 3500))

    async def predict_career_paths(self, parsed_resume: dict, job_description: str = "") -> dict:
        system = "You are a career counselor. Return ONLY valid JSON."
        user = f"""Predict career paths for this candidate.

SKILLS: {', '.join(parsed_resume.get('skills', [])[:20])}
EXPERIENCE: {json.dumps([e.get('title','') for e in parsed_resume.get('experience', [])[:3]])}
EDUCATION: {json.dumps([e.get('degree','') for e in parsed_resume.get('education', [])[:2]])}
{"JD: " + job_description[:600] if job_description else ""}

Return ONLY this JSON:
{{
  "current_level": "Mid-Level",
  "next_steps": ["action1", "action2", "action3"],
  "target_roles": [
    {{
      "title": "role",
      "match_percentage": 85.0,
      "required_skills": ["skill1"],
      "skill_gap": ["missing"],
      "avg_salary": "$90,000 - $130,000",
      "growth_outlook": "Excellent",
      "description": "2 sentence description"
    }}
  ],
  "timeline_months": 6,
  "key_milestones": ["milestone1", "milestone2"]
}}

Include 3 different target roles."""
        return self._parse_json(await self._call_groq(system, user, 2000))

    async def suggest_projects(self, missing_skills: list, current_skills: list, target_role: str) -> list:
        system = "You are a software engineering mentor. Return ONLY a valid JSON array."
        user = f"""Suggest 4 portfolio projects.

MISSING SKILLS: {', '.join(missing_skills[:8])}
CURRENT SKILLS: {', '.join(current_skills[:10])}
TARGET ROLE: {target_role}

Return ONLY a JSON array:
[
  {{
    "name": "project name",
    "description": "what it does and why it matters",
    "skills_practiced": ["skill1", "skill2"],
    "difficulty": "medium",
    "estimated_hours": 40,
    "github_template": null,
    "why_relevant": "why this impresses interviewers"
  }}
]"""
        return self._parse_json_array(await self._call_groq(system, user, 1800))

    async def rewrite_resume(self, parsed_resume: dict, target_role: str, tone: str = "professional") -> str:
        system = "You are an elite resume writer. Output clean formatted text only, no JSON."
        user = f"""Rewrite this resume for: {target_role} ({tone} tone)

Name: {parsed_resume.get('name')}
Email: {parsed_resume.get('email')}
Skills: {', '.join(parsed_resume.get('skills', []))}
Experience: {json.dumps(parsed_resume.get('experience', [])[:3], indent=2)[:2000]}
Education: {json.dumps(parsed_resume.get('education', []), indent=2)[:500]}
Projects: {json.dumps(parsed_resume.get('projects', [])[:3], indent=2)[:800]}

Write a complete ATS-friendly resume with: Header, Professional Summary, Technical Skills, Work Experience (quantified bullets), Education, Projects."""
        return await self._call_groq(system, user, 3000)

    async def resume_chat(self, message: str, resume_context: dict, history: list, job_description: str = "") -> dict:
        system = (
            f"You are PathNova AI, an intelligent career assistant with full access to the candidate's resume. "
            f"Be specific and actionable.\n\n"
            f"RESUME: Name={resume_context.get('name')}, "
            f"Skills={', '.join(resume_context.get('skills', [])[:20])}, "
            f"Experience={json.dumps([e.get('title','') for e in resume_context.get('experience', [])[:3]])}\n"
            f"{'JD: ' + job_description[:400] if job_description else ''}"
        )
        messages = [{"role": "system", "content": system}]
        for msg in history[-8:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        payload = {"model": MODEL, "max_tokens": 1024, "temperature": 0.5, "messages": messages}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(GROQ_API_URL, headers=self.headers, json=payload)
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"]

        # Suggestions
        try:
            sp = {"model": MODEL, "max_tokens": 200, "temperature": 0.4, "messages": [
                {"role": "system", "content": "Return ONLY a JSON array of 3 short follow-up question strings."},
                {"role": "user", "content": f"Suggest 3 follow-up questions based on: '{reply[:200]}'"},
            ]}
            async with httpx.AsyncClient(timeout=15.0) as client:
                sr = await client.post(GROQ_API_URL, headers=self.headers, json=sp)
                suggestions = self._parse_json_array(sr.json()["choices"][0]["message"]["content"])
        except Exception:
            suggestions = ["What are my strongest skills?", "How can I improve my ATS score?", "What jobs suit me?"]

        return {"response": reply, "suggestions": suggestions}


ai_service = AIAnalysisService()
