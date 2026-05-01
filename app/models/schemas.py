"""
Pydantic models for request/response validation.
All API I/O is strongly typed here.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class QuestionCategory(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    HR = "hr"
    SITUATIONAL = "situational"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ─── Resume Parsing ────────────────────────────────────────────────────────────

class Education(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    gpa: Optional[str] = None
    field: Optional[str] = None


class WorkExperience(BaseModel):
    title: str
    company: str
    duration: str
    description: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Project(BaseModel):
    name: str
    description: str
    technologies: List[str]
    impact: Optional[str] = None
    url: Optional[str] = None


class ParsedResume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    education: List[Education] = []
    experience: List[WorkExperience] = []
    projects: List[Project] = []
    certifications: List[str] = []
    languages: List[str] = []
    raw_text: str = ""


# ─── ATS Score ────────────────────────────────────────────────────────────────

class ATSScoreBreakdown(BaseModel):
    skills_match: float = Field(..., ge=0, le=100)
    experience_relevance: float = Field(..., ge=0, le=100)
    formatting_score: float = Field(..., ge=0, le=100)
    keyword_density: float = Field(..., ge=0, le=100)
    semantic_similarity: float = Field(..., ge=0, le=100)


class ATSScore(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    breakdown: ATSScoreBreakdown
    matched_keywords: List[str]
    missing_keywords: List[str]
    grade: str  # A+, A, B+, B, C, D
    summary: str


# ─── Skill Gap ────────────────────────────────────────────────────────────────

class SkillGapItem(BaseModel):
    skill: str
    importance: str  # critical, important, nice-to-have
    current_level: Optional[str] = None
    required_level: str
    learning_time_weeks: int


class SkillGapAnalysis(BaseModel):
    matching_skills: List[str]
    missing_skills: List[SkillGapItem]
    weak_skills: List[str]
    overqualified_areas: List[str]
    match_percentage: float
    strengths: List[str]
    weaknesses: List[str]


# ─── Section Feedback ─────────────────────────────────────────────────────────

class SectionScore(BaseModel):
    section: str
    score: float
    feedback: str
    suggestions: List[str]


class SectionFeedback(BaseModel):
    sections: List[SectionScore]
    overall_impression: str
    top_improvements: List[str]


# ─── AI Suggestions ───────────────────────────────────────────────────────────

class BulletImprovement(BaseModel):
    original: str
    improved: str
    reason: str


class AISuggestions(BaseModel):
    summary_rewrite: Optional[str] = None
    bullet_improvements: List[BulletImprovement]
    action_verb_suggestions: List[str]
    quantification_tips: List[str]
    formatting_tips: List[str]
    keywords_to_add: List[str]


# ─── Learning Roadmap ─────────────────────────────────────────────────────────

class Resource(BaseModel):
    title: str
    type: str  # course, video, article, book
    url: Optional[str] = None
    platform: Optional[str] = None
    duration: Optional[str] = None
    free: bool = True


class RoadmapWeek(BaseModel):
    week: int
    title: str
    skill: str
    topics: List[str]
    projects: List[str]
    resources: List[Resource]
    estimated_hours: int


class LearningRoadmap(BaseModel):
    total_weeks: int
    target_role: str
    weeks: List[RoadmapWeek]
    milestones: List[str]
    priority_skills: List[str]


# ─── Interview Questions ──────────────────────────────────────────────────────

class InterviewQuestion(BaseModel):
    id: int
    question: str
    category: QuestionCategory
    difficulty: Difficulty
    skill_tested: str
    expected_answer_points: List[str]
    follow_up: Optional[str] = None


class InterviewQuestionsResponse(BaseModel):
    questions: List[InterviewQuestion]
    total: int
    role_targeted: str
    focus_areas: List[str]


# ─── Career Predictions ───────────────────────────────────────────────────────

class CareerRole(BaseModel):
    title: str
    match_percentage: float
    required_skills: List[str]
    skill_gap: List[str]
    avg_salary: str
    growth_outlook: str
    description: str


class CareerPath(BaseModel):
    current_level: str
    next_steps: List[str]
    target_roles: List[CareerRole]
    timeline_months: int
    key_milestones: List[str]


# ─── Project Suggestions ──────────────────────────────────────────────────────

class ProjectSuggestion(BaseModel):
    name: str
    description: str
    skills_practiced: List[str]
    difficulty: Difficulty
    estimated_hours: int
    github_template: Optional[str] = None
    why_relevant: str


# ─── GitHub Analysis ──────────────────────────────────────────────────────────

class RepoAnalysis(BaseModel):
    name: str
    language: str
    stars: int
    description: Optional[str] = None
    topics: List[str]
    last_updated: str
    quality_score: float
    suggestions: List[str]


class GitHubAnalysis(BaseModel):
    username: str
    public_repos: int
    total_stars: int
    languages: Dict[str, int]
    top_repos: List[RepoAnalysis]
    profile_score: float
    strengths: List[str]
    improvements: List[str]
    skills_demonstrated: List[str]


# ─── Full Analysis Response ───────────────────────────────────────────────────

class FullAnalysisResponse(BaseModel):
    session_id: str
    parsed_resume: ParsedResume
    ats_score: ATSScore
    skill_gap: SkillGapAnalysis
    section_feedback: SectionFeedback
    ai_suggestions: AISuggestions
    learning_roadmap: LearningRoadmap
    interview_questions: InterviewQuestionsResponse
    career_paths: CareerPath
    project_suggestions: List[ProjectSuggestion]


# ─── Chatbot ──────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []


# ─── Request Bodies ───────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    session_id: str
    job_description: Optional[str] = None
    job_url: Optional[str] = None
    target_role: Optional[str] = None


class ResumeRewriteRequest(BaseModel):
    session_id: str
    target_role: str
    tone: str = "professional"  # professional, creative, technical


class GitHubAnalyzeRequest(BaseModel):
    github_url: str
    session_id: Optional[str] = None
