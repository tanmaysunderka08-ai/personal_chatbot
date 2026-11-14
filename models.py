
from pydantic import BaseModel, Field, field_validator

class Experience(BaseModel):
    company: str
    role: str
    start_date: str | None = None
    end_date: str | None = None
    description: list[str] = []
    skills_used: list[str] = []
 
 
class Project(BaseModel):
    name: str
    description: list[str] = []
    skills_used: list[str] = []
    links: list[str] = []
 
 
class Education(BaseModel):
    institution: str
    degree: str | None = None
    start_year: str | None = None
    end_year: str | None = None
    grade: str | None = None
 
 
class Resume(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    experiences: list[Experience] = []
    skills: list[str] = []
    projects: list[Project] = []
    education: list[Education] = []

class JobDesc(BaseModel):
    role: str | None = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    minimum_experience: int | None = None
    education: str | None = None
    responsibilities: list[str] = []

    @field_validator("required_skills", "preferred_skills", "responsibilities", mode="before")
    @classmethod
    def none_to_empty(cls, v):
        return v or []


class MatchResult(BaseModel):
    score: float = Field(default=0, ge=0, le=100)
    name: str
    matched_skills: list[str] = []
    missing_skills: list[str] = []

    @field_validator("matched_skills", "missing_skills", mode="before")
    @classmethod
    def none_to_empty(cls, v):
        return v or []