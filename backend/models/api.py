from pydantic import BaseModel

from backend.models.analysis import (
    Gap,
    JobRequirements,
    Recommendations,
    Strength,
    AgentAction,
)


class AnalyzeResponse(BaseModel):
    resume_id: int
    filename: str
    job: JobRequirements
    match_score: float
    strengths: list[Strength]
    gaps: list[Gap]
    recommendations: Recommendations
    agent_actions: list[AgentAction]