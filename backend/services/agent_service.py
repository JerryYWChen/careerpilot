from backend.agents.graph import career_agent
from backend.models.analysis import AgentAction, Gap


def generate_agent_actions(gaps: list[Gap]) -> list[AgentAction]:
    actions = []

    for gap in gaps:
        initial_state = {
            "current_gap": gap,
            "action_type": None,
            "recommendation": None,
            "review_passed": None,
            "review_feedback": None,
            "retry_count": 0,
        }

        result = career_agent.invoke(initial_state)

        action = AgentAction(
            gap=gap.area,
            action_type=result["action_type"],
            recommendation=result["recommendation"],
            review_passed=result["review_passed"],
            retry_count=result["retry_count"],
        )

        actions.append(action)

    return actions