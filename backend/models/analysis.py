from enum import Enum

from pydantic import BaseModel

class RequirementCategory(str, Enum):
    SKILL = "skill"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CERTIFICATION = "certification"


class RequirementImportance(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"


class SeniorityLevel(str, Enum):
    INTERN = "intern"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    UNKNOWN = "unknown"

class Requirement(BaseModel):
    name: str
    category: RequirementCategory
    importance: RequirementImportance
    minimum_years: float | None = None


class JobRequirements(BaseModel):
    job_title: str
    seniority_level: SeniorityLevel
    summary: str
    requirements: list[Requirement]

class MatchStatus(str, Enum):
    MATCHED = "matched"
    PARTIAL = "partial"
    MISSING = "missing"

class EvidenceSource(str, Enum):
    SKILLS = "skills"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    RESEARCH = "research"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"

class RequirementMatch(BaseModel):
    requirement_name: str
    status: MatchStatus
    evidence: str | None = None
    evidence_sources: list[EvidenceSource]
    reason: str

class ResumeMatchResult(BaseModel):
    matches: list[RequirementMatch]

class Strength(BaseModel):
    area: str
    evidence: str
    reason: str


class Gap(BaseModel):
    area: str
    status: MatchStatus
    evidence: str | None = None
    reason: str


class MatchAnalysis(BaseModel):
    strengths: list[Strength]
    gaps: list[Gap]

class Recommendations(BaseModel):
    highlight: list[str]
    strengthen: list[str]
