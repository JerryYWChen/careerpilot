from unittest.mock import patch

from backend.models.analysis import (
    CareerActionPlan,
    Gap,
    MatchStatus,
    PlannedAction,
)
from backend.services.planner_service import (
    create_validated_career_action_plan,
)
import pytest

def test_valid_plan_returns_without_retry():
    gaps = [
        Gap(
            area="Docker",
            status=MatchStatus.MISSING,
            evidence=None,
            reason="No Docker evidence.",
        )
    ]

    valid_plan = CareerActionPlan(
        actions=[
            PlannedAction(
                title="Learn Docker",
                description="Containerize an existing project.",
                addresses_gaps=["Docker"],
                priority=1,
                depends_on=[],
            )
        ]
    )

    with patch(
        "backend.services.planner_service.generate_career_action_plan",
        return_value=valid_plan,
    ) as mock_generate:

        result = create_validated_career_action_plan(gaps)

    assert result == valid_plan
    assert mock_generate.call_count == 1

def test_invalid_plan_retries_then_returns_valid_plan():
    gaps = [
        Gap(
            area="Docker",
            status=MatchStatus.MISSING,
            evidence=None,
            reason="No Docker evidence.",
        )
    ]

    invalid_plan = CareerActionPlan(
        actions=[
            PlannedAction(
                title="Learn Docker",
                description="Containerize an existing project.",
                addresses_gaps=["Docker (missing)"],  # invalid
                priority=1,
                depends_on=[],
            )
        ]
    )

    valid_plan = CareerActionPlan(
        actions=[
            PlannedAction(
                title="Learn Docker",
                description="Containerize an existing project.",
                addresses_gaps=["Docker"],
                priority=1,
                depends_on=[],
            )
        ]
    )

    with patch(
        "backend.services.planner_service.generate_career_action_plan",
        side_effect=[invalid_plan, valid_plan],
    ) as mock_generate:

        result = create_validated_career_action_plan(gaps)

    assert result == valid_plan
    assert mock_generate.call_count == 2

def test_validation_feedback_reaches_next_attempt():
    gaps = [
        Gap(
            area="Docker",
            status=MatchStatus.MISSING,
            evidence=None,
            reason="No Docker evidence.",
        )
    ]

    invalid_plan = CareerActionPlan(
        actions=[
            PlannedAction(
                title="Learn Docker",
                description="Containerize an existing project.",
                addresses_gaps=["Docker (missing)"],
                priority=1,
                depends_on=[],
            )
        ]
    )

    valid_plan = CareerActionPlan(
        actions=[
            PlannedAction(
                title="Learn Docker",
                description="Containerize an existing project.",
                addresses_gaps=["Docker"],
                priority=1,
                depends_on=[],
            )
        ]
    )

    with patch(
        "backend.services.planner_service.generate_career_action_plan",
        side_effect=[invalid_plan, valid_plan],
    ) as mock_generate:

        result = create_validated_career_action_plan(gaps)

    assert result == valid_plan
    assert mock_generate.call_count == 2

    first_call = mock_generate.call_args_list[0]
    second_call = mock_generate.call_args_list[1]

    assert first_call.kwargs["validation_feedback"] is None

    assert (
        second_call.kwargs["validation_feedback"]
        == "Unknown gap 'Docker (missing)' in action 'Learn Docker'."
    )

def test_max_attempts_exhausted_raises_error():
    gaps = [
        Gap(
            area="Docker",
            status=MatchStatus.MISSING,
            evidence=None,
            reason="No Docker evidence.",
        )
    ]

    invalid_plan = CareerActionPlan(
        actions=[
            PlannedAction(
                title="Learn Docker",
                description="Containerize an existing project.",
                addresses_gaps=["Docker (missing)"],
                priority=1,
                depends_on=[],
            )
        ]
    )

    with patch(
        "backend.services.planner_service.generate_career_action_plan",
        return_value=invalid_plan,
    ) as mock_generate:

        with pytest.raises(
            ValueError,
            match="after 3 attempts",
        ):
            create_validated_career_action_plan(
                gaps,
                max_attempts=3,
            )

    assert mock_generate.call_count == 3