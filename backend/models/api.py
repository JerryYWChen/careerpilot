from pydantic import BaseModel

from backend.models.analysis import (
    Gap,
    JobRequirements,
    NotAssessableRequirement,
    ResumeHighlights,
    Strength,
    CareerActionPlan,
)


class AnalyzeResponse(BaseModel):
    resume_id: int
    filename: str
    job: JobRequirements
    match_score: float
    strengths: list[Strength]
    gaps: list[Gap]
    not_assessable: list[NotAssessableRequirement]
    resume_highlights: ResumeHighlights
    career_action_plan: CareerActionPlan
