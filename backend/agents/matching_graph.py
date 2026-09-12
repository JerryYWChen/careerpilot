from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.models.analysis import JobRequirements, ResumeMatchResult
from backend.services import ai_service
from backend.services.scoring_service import validate_resume_match_result


MAX_MATCH_ATTEMPTS = 3


class ResumeMatchingState(TypedDict):
    resume_text: str
    job_requirements: JobRequirements
    match_result: ResumeMatchResult | None
    validation_feedback: str | None
    attempt_count: int


def generate_match_node(state: ResumeMatchingState):
    match_result = ai_service._generate_resume_match_result(
        state["resume_text"],
        state["job_requirements"],
        validation_feedback=state["validation_feedback"],
    )

    return {
        "match_result": match_result,
        "attempt_count": state["attempt_count"] + 1,
    }


def validate_match_node(state: ResumeMatchingState):
    try:
        validate_resume_match_result(
            state["match_result"],
            state["job_requirements"],
        )
        return {"validation_feedback": None}

    except ValueError as error:
        return {"validation_feedback": str(error)}


def route_after_validation(state: ResumeMatchingState):
    if state["validation_feedback"] is None:
        return "complete"

    if state["attempt_count"] < MAX_MATCH_ATTEMPTS:
        return "retry"

    return "failed"


def raise_match_validation_error(state: ResumeMatchingState):
    raise ValueError(
        f"Failed to generate a valid resume match result "
        f"after {MAX_MATCH_ATTEMPTS} attempts. "
        f"Last error: {state['validation_feedback']}"
    )


builder = StateGraph(ResumeMatchingState)
builder.add_node("generate_match", generate_match_node)
builder.add_node("validate_match", validate_match_node)
builder.add_node("raise_validation_error", raise_match_validation_error)

builder.add_edge(START, "generate_match")
builder.add_edge("generate_match", "validate_match")
builder.add_conditional_edges(
    "validate_match",
    route_after_validation,
    {
        "complete": END,
        "retry": "generate_match",
        "failed": "raise_validation_error",
    },
)

resume_matching_graph = builder.compile()
