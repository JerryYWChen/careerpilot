from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.models.analysis import CareerActionPlan, Gap
from backend.services import planner_service


MAX_PLAN_ATTEMPTS = 3


class CareerPlanState(TypedDict):
    gaps: list[Gap]
    career_action_plan: CareerActionPlan | None
    validation_feedback: str | None
    attempt_count: int


def generate_plan_node(state: CareerPlanState):
    plan = planner_service.generate_career_action_plan(
        state["gaps"],
        validation_feedback=state["validation_feedback"],
    )

    return {
        "career_action_plan": plan,
        "attempt_count": state["attempt_count"] + 1,
    }


def validate_plan_node(state: CareerPlanState):
    try:
        planner_service.validate_career_action_plan(
            state["career_action_plan"],
            state["gaps"],
        )
        return {"validation_feedback": None}

    except ValueError as error:
        return {"validation_feedback": str(error)}


def route_after_validation(state: CareerPlanState):
    if state["validation_feedback"] is None:
        return "complete"

    if state["attempt_count"] < MAX_PLAN_ATTEMPTS:
        return "retry"

    return "failed"


def raise_plan_validation_error(state: CareerPlanState):
    raise ValueError(
        f"Failed to generate a valid career action plan "
        f"after {MAX_PLAN_ATTEMPTS} attempts. "
        f"Last error: {state['validation_feedback']}"
    )


builder = StateGraph(CareerPlanState)
builder.add_node("generate_plan", generate_plan_node)
builder.add_node("validate_plan", validate_plan_node)
builder.add_node("raise_validation_error", raise_plan_validation_error)

builder.add_edge(START, "generate_plan")
builder.add_edge("generate_plan", "validate_plan")
builder.add_conditional_edges(
    "validate_plan",
    route_after_validation,
    {
        "complete": END,
        "retry": "generate_plan",
        "failed": "raise_validation_error",
    },
)

career_plan_graph = builder.compile()
