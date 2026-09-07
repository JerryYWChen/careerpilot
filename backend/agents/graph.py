from langgraph.graph import StateGraph, START, END

from backend.agents.state import CareerAgentState
from backend.agents.nodes import (
    route_gap,
    choose_action,
    resume_improvement_node,
    skill_development_node,
    review_recommendation_node,
    choose_review_action,
    increment_retry_node,
)

builder = StateGraph(CareerAgentState)
builder.add_node("route_gap", route_gap)
builder.add_node("resume_improvement", resume_improvement_node)
builder.add_node("skill_development", skill_development_node)
builder.add_node("review_recommendation", review_recommendation_node)
builder.add_node("increment_retry", increment_retry_node)

builder.add_edge(START, "route_gap")

builder.add_conditional_edges(
    "route_gap",
    choose_action,
    {
        "resume_improvement": "resume_improvement",
        "skill_development": "skill_development",
    }
)

builder.add_edge(
    "resume_improvement",
    "review_recommendation"
)

builder.add_edge(
    "skill_development",
    "review_recommendation"
)

builder.add_conditional_edges(
    "review_recommendation",
    choose_review_action,
    {
        "end": END,
        "retry": "increment_retry",
    }
)

builder.add_conditional_edges(
    "increment_retry",
    choose_action,
    {
        "resume_improvement": "resume_improvement",
        "skill_development": "skill_development",
    }
)

career_agent = builder.compile()