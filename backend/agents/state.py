from typing import TypedDict

from backend.models.analysis import Gap


class CareerAgentState(TypedDict):
    current_gap: Gap
    action_type: str | None
    recommendation: str | None
    review_passed: bool | None
    review_feedback: str | None
    retry_count: int