from backend.agents.state import CareerAgentState
from backend.models.analysis import MatchStatus
from backend.services.ai_service import (
    generate_resume_improvement,
    generate_skill_development,
    review_recommendation,
)

def route_gap(state: CareerAgentState):
    status = state["current_gap"].status

    if status == MatchStatus.PARTIAL:
        return {"action_type": "resume_improvement"}

    if status == MatchStatus.MISSING:
        return {"action_type": "skill_development"}

    raise ValueError(
        f"Unexpected gap status: {status}"
    )

def resume_improvement_node(state: CareerAgentState):
    recommendation = generate_resume_improvement(
        state["current_gap"],
        state["review_feedback"]
    )

    return {
        "recommendation": recommendation
    }

def skill_development_node(state: CareerAgentState):
    recommendation = generate_skill_development(
        state["current_gap"],
        state["review_feedback"]
    )

    return {
        "recommendation": recommendation
    }

def review_recommendation_node(state: CareerAgentState):
    review = review_recommendation(
        state["current_gap"],
        state["recommendation"]
    )

    return {
        "review_passed": review.passed,
        "review_feedback": review.feedback,
    }

def choose_action(state: CareerAgentState):
    return state["action_type"]

def choose_review_action(state: CareerAgentState):
    if state["review_passed"]:
        return "end"

    if state["retry_count"] >= 2:
        return "end"

    return "retry"


def increment_retry_node(state: CareerAgentState):
    return {
        "retry_count": state["retry_count"] + 1
    }