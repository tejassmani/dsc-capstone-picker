from pydantic import BaseModel


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


class StudentProfile(BaseModel):
    interests: list[str] = []
    skills: list[str] = []
    preferences: list[str] = []
    raw_text: str = ""