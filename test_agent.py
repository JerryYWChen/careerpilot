# from backend.agents.graph import career_agent
# from backend.models.analysis import Gap, MatchStatus


# # gap = Gap(
# #     area="AWS",
# #     status=MatchStatus.PARTIAL,
# #     evidence="AWS listed in skills section",
# #     reason="AWS is mentioned, but there is limited project evidence."
# # )

# gap = Gap(
#     area="Kubernetes",
#     status=MatchStatus.MISSING,
#     evidence=None,
#     reason="No Kubernetes experience is shown in the resume."
# )

# state = {
#     "current_gap": gap,
#     "action_type": None,
#     "recommendation": None,
#     "review_passed": None,
#     "review_feedback": None,
#     "retry_count": 0
# }

# result = career_agent.invoke(state)

# print(result)

from backend.models.analysis import Gap, MatchStatus
from backend.services.agent_service import generate_agent_actions


gaps = [
    Gap(
        area="AWS",
        status=MatchStatus.PARTIAL,
        evidence="AWS listed in skills section",
        reason="AWS is mentioned, but there is limited project evidence.",
    ),
    Gap(
        area="Kubernetes",
        status=MatchStatus.MISSING,
        evidence=None,
        reason="No Kubernetes experience is shown in the resume.",
    ),
]


actions = generate_agent_actions(gaps)

for action in actions:
    print(action)