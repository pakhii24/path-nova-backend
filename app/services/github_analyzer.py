"""
GitHub Profile Analyzer Service
Fetches public GitHub data and scores the profile for recruiters.
"""

import logging
import httpx
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubAnalyzerService:

    def __init__(self):
        self.headers = {"Accept": "application/vnd.github+json"}
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    def _extract_username(self, url: str) -> str:
        """Parse github.com/username from a URL or bare username."""
        url = url.strip().rstrip("/")
        if "github.com/" in url:
            return url.split("github.com/")[-1].split("/")[0]
        return url

    async def analyze(self, github_url: str) -> dict:
        username = self._extract_username(github_url)
        async with httpx.AsyncClient(timeout=15.0) as client:
            # User profile
            user_resp = await client.get(f"{GITHUB_API}/users/{username}", headers=self.headers)
            if user_resp.status_code == 404:
                raise ValueError(f"GitHub user '{username}' not found")
            user_resp.raise_for_status()
            user = user_resp.json()

            # Repos
            repos_resp = await client.get(
                f"{GITHUB_API}/users/{username}/repos",
                headers=self.headers,
                params={"sort": "updated", "per_page": 30, "type": "owner"},
            )
            repos_resp.raise_for_status()
            repos = repos_resp.json()

        # Aggregate language stats
        languages: dict = {}
        total_stars = 0
        top_repos = []

        for repo in repos:
            if repo.get("fork"):
                continue
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            stars = repo.get("stargazers_count", 0)
            total_stars += stars

            quality_score = self._score_repo(repo)
            suggestions = self._repo_suggestions(repo)

            top_repos.append({
                "name": repo["name"],
                "language": lang or "Unknown",
                "stars": stars,
                "description": repo.get("description"),
                "topics": repo.get("topics", []),
                "last_updated": repo.get("updated_at", "")[:10],
                "quality_score": quality_score,
                "suggestions": suggestions,
            })

        # Sort by quality score
        top_repos = sorted(top_repos, key=lambda r: r["quality_score"], reverse=True)[:6]

        profile_score = self._score_profile(user, repos, total_stars)
        strengths, improvements = self._profile_insights(user, repos, languages, total_stars)
        skills_demonstrated = list(languages.keys())[:10]

        return {
            "username": username,
            "public_repos": user.get("public_repos", 0),
            "total_stars": total_stars,
            "languages": languages,
            "top_repos": top_repos,
            "profile_score": profile_score,
            "strengths": strengths,
            "improvements": improvements,
            "skills_demonstrated": skills_demonstrated,
        }

    def _score_repo(self, repo: dict) -> float:
        score = 50.0
        if repo.get("description"):
            score += 10
        if repo.get("topics"):
            score += min(len(repo["topics"]) * 3, 15)
        if repo.get("stargazers_count", 0) > 0:
            score += min(repo["stargazers_count"] * 2, 20)
        if repo.get("has_wiki"):
            score += 5
        if not repo.get("archived"):
            score += 5
        return min(score, 100.0)

    def _repo_suggestions(self, repo: dict) -> list:
        suggestions = []
        if not repo.get("description"):
            suggestions.append("Add a description to explain what this project does")
        if not repo.get("topics"):
            suggestions.append("Add topic tags to improve discoverability")
        if repo.get("stargazers_count", 0) == 0:
            suggestions.append("Share this project to gain visibility")
        if not repo.get("homepage"):
            suggestions.append("Add a live demo link if available")
        return suggestions[:3]

    def _score_profile(self, user: dict, repos: list, total_stars: int) -> float:
        score = 30.0
        if user.get("bio"):
            score += 10
        if user.get("blog"):
            score += 5
        if user.get("location"):
            score += 5
        active_repos = [r for r in repos if not r.get("fork") and r.get("language")]
        score += min(len(active_repos) * 2, 20)
        score += min(total_stars * 1.5, 25)
        if user.get("followers", 0) > 10:
            score += 5
        return min(round(score, 1), 100.0)

    def _profile_insights(self, user, repos, languages, total_stars):
        strengths, improvements = [], []

        active = [r for r in repos if not r.get("fork") and r.get("language")]
        if len(active) >= 5:
            strengths.append(f"Active portfolio with {len(active)} original repositories")
        if len(languages) >= 3:
            strengths.append(f"Polyglot developer proficient in {', '.join(list(languages.keys())[:4])}")
        if total_stars > 10:
            strengths.append(f"Community recognition with {total_stars} total stars")
        if user.get("bio"):
            strengths.append("Clear professional bio on profile")

        if not user.get("bio"):
            improvements.append("Write a compelling bio highlighting your expertise")
        if not user.get("blog"):
            improvements.append("Add your portfolio or LinkedIn URL to your profile")
        if len(active) < 3:
            improvements.append("Add more original projects to showcase your skills")
        repos_with_desc = [r for r in active if r.get("description")]
        if len(repos_with_desc) < len(active) / 2:
            improvements.append("Add descriptions to all your repositories")

        return strengths[:4], improvements[:4]


github_analyzer = GitHubAnalyzerService()
