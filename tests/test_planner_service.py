from unittest.mock import patch

from backend.models.analysis import (
    CareerActionPlan,
    Gap,
    MatchStatus,
    PlannedAction,
)
from backend.rag.models import PlanKnowledgeChunk
from backend.services.planner_service import (
    create_validated_career_action_plan,
)
import pytest


@pytest.fixture(autouse=True)
def mock_planning_retrieval():
    with patch(
        "backend.services.planner_service.retrieve_planning_context",
        return_value=[],
    ) as mock_retrieve:
        yield mock_retrieve

def test_langgraph_returns_valid_plan_without_retry():
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

def test_langgraph_retries_invalid_plan_then_returns_valid_plan():
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

def test_langgraph_passes_validation_feedback_to_next_attempt():
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

def test_langgraph_max_attempts_exhausted_raises_error():
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
            create_validated_career_action_plan(gaps)

    assert mock_generate.call_count == 3

def test_empty_gaps_returns_empty_plan_without_generation():
    gaps = []

    with patch(
        "backend.services.planner_service.generate_career_action_plan",
    ) as mock_generate:

        result = create_validated_career_action_plan(gaps)

    assert result.actions == []
    mock_generate.assert_not_called()


def test_retrieval_happens_once_and_context_is_fixed_across_retries(
    mock_planning_retrieval,
):
    gaps = [
        Gap(
            area="Docker",
            status=MatchStatus.MISSING,
            evidence=None,
            reason="No Docker evidence.",
        )
    ]
    context = [
        PlanKnowledgeChunk(
            chunk_id="container-practice",
            document_title="Container Guide",
            section="Practice",
            content="Containerize a small service.",
            score=0.82,
            relevant_gaps=("Docker",),
        )
    ]
    mock_planning_retrieval.return_value = context
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
    mock_planning_retrieval.assert_called_once_with(gaps)
    assert mock_generate.call_count == 2
    assert mock_generate.call_args_list[0].kwargs["retrieved_context"] == context
    assert mock_generate.call_args_list[1].kwargs["retrieved_context"] == context


def test_empty_retrieval_context_falls_back_to_existing_planner(
    mock_planning_retrieval,
):
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
    mock_planning_retrieval.assert_called_once_with(gaps)
    mock_generate.assert_called_once_with(
        gaps,
        validation_feedback=None,
        retrieved_context=[],
    )


def test_retrieved_context_is_passed_to_generation_but_not_validation(
    mock_planning_retrieval,
):
    gaps = [
        Gap(
            area="Docker",
            status=MatchStatus.MISSING,
            evidence=None,
            reason="No Docker evidence.",
        )
    ]
    context = [
        PlanKnowledgeChunk(
            chunk_id="container-practice",
            document_title="Container Guide",
            section="Practice",
            content="Containerize a small service.",
            score=0.82,
            relevant_gaps=("Docker",),
        )
    ]
    mock_planning_retrieval.return_value = context
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

    with (
        patch(
            "backend.services.planner_service.generate_career_action_plan",
            return_value=valid_plan,
        ) as mock_generate,
        patch(
            "backend.services.planner_service.validate_career_action_plan",
        ) as mock_validate,
    ):
        result = create_validated_career_action_plan(gaps)

    assert result == valid_plan
    mock_generate.assert_called_once_with(
        gaps,
        validation_feedback=None,
        retrieved_context=context,
    )
    mock_validate.assert_called_once_with(valid_plan, gaps)
