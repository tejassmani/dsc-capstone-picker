import json
from pathlib import Path

from pydantic import BaseModel, Field

DOMAINS_PATH = Path("domains.json")
PROFILE_PATH = Path("profile.json")


class CapstoneDomain(BaseModel):
    title: str
    mentor: str | None = None
    section: str | None = None
    seats: int | None = None
    meeting_time: str | None = None
    industry_partner: bool = False
    topic_area: str | None = None
    description: str = ""
    prerequisites: str = ""
    mentor_style: str = ""
    summer_tasks: str = ""
    previous_projects: str = ""
    url: str | None = None
    raw_text: str = ""


class StudentProfile(BaseModel):
    interests: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    career_goals: list[str] = Field(default_factory=list)
    resume_text: str = ""
    raw_text: str = ""


class Recommendation(BaseModel):
    domain: CapstoneDomain
    score: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    llm_explanation: str = ""


def save_domains(domains: list[CapstoneDomain], path: str | Path = DOMAINS_PATH) -> None:
    """Save capstone domains to a local JSON file."""
    destination = Path(path)
    data = [domain.model_dump(mode="json") for domain in domains]
    destination.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_domains(path: str | Path = DOMAINS_PATH) -> list[CapstoneDomain]:
    """Load capstone domains from a local JSON file."""
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    return [CapstoneDomain.model_validate(item) for item in data]


def save_profile(profile: StudentProfile, path: str | Path = PROFILE_PATH) -> None:
    """Save a student profile to a local JSON file."""
    destination = Path(path)
    destination.write_text(
        json.dumps(profile.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )


def load_profile(path: str | Path = PROFILE_PATH) -> StudentProfile:
    """Load a student profile from a local JSON file."""
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    return StudentProfile.model_validate(data)
