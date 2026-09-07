from backend.models.analysis import Gap, MatchStatus
from backend.services.planner_service import (
    create_validated_career_action_plan,
)

gaps = [
    Gap(
        area="AWS cloud services",
        status=MatchStatus.MISSING,
        evidence=None,
        reason="The resume does not mention AWS."
    ),
    Gap(
        area="Docker",
        status=MatchStatus.MISSING,
        evidence=None,
        reason="The resume does not mention Docker."
    ),
    Gap(
        area="Kubernetes",
        status=MatchStatus.MISSING,
        evidence=None,
        reason="The resume does not mention Kubernetes."
    ),
    Gap(
        area="Software engineering experience",
        status=MatchStatus.PARTIAL,
        evidence="Recent software-oriented projects are shown.",
        reason="The resume does not establish at least three years of experience."
    ),
]

plan = create_validated_career_action_plan(gaps)

print("PLAN VALID")
print(plan)