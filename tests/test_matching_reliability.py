from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.agents.matching_graph import run_resume_matching_workflow
from backend.models.analysis import (
    JobRequirements,
    MatchStatus,
    Requirement,
    RequirementMatch,
    ResumeMatchResult,
)
from backend.services.ai_service import (
    MATCH_PROMPT_VERSION,
    MATCH_SYSTEM_PROMPTS,
    MATCH_V1_SYSTEM_PROMPT,
    MATCH_V2_SYSTEM_PROMPT,
    MATCH_V3_SYSTEM_PROMPT,
    MODEL_NAME,
    match_resume_to_requirements,
)
from backend.services.scoring_service import validate_resume_match_result


def make_requirements(*names: str) -> JobRequirements:
    return JobRequirements(
        job_title="Backend Engineer",
        seniority_level="unknown",
        summary="Test requirements.",
        requirements=[
            Requirement(
                name=name,
                category="skill",
                importance="required",
            )
            for name in names
        ],
    )


def make_match(name: str) -> RequirementMatch:
    return RequirementMatch(
        requirement_name=name,
        status=MatchStatus.MISSING,
        evidence=None,
        evidence_sources=[],
        reason="No evidence found.",
    )


def test_validator_accepts_exact_case_insensitive_coverage():
    requirements = make_requirements("Python", "Docker")
    result = ResumeMatchResult(
        matches=[make_match("python"), make_match("DOCKER")]
    )

    validate_resume_match_result(result, requirements)


def test_validator_rejects_missing_match():
    requirements = make_requirements("Python", "Docker")
    result = ResumeMatchResult(matches=[make_match("Python")])

    with pytest.raises(
        ValueError,
        match=r"Missing matches for requirements: \['Docker'\]",
    ):
        validate_resume_match_result(result, requirements)


def test_validator_rejects_case_insensitive_duplicate_match():
    requirements = make_requirements("Python")
    result = ResumeMatchResult(
        matches=[make_match("Python"), make_match("PYTHON")]
    )

    with pytest.raises(
        ValueError,
        match=r"Duplicate matches for requirements: \['Python'\]",
    ):
        validate_resume_match_result(result, requirements)


def test_validator_rejects_unknown_match():
    requirements = make_requirements("Python")
    result = ResumeMatchResult(
        matches=[make_match("Python"), make_match("Docker")]
    )

    with pytest.raises(
        ValueError,
        match=r"Unknown matches: \['Docker'\]",
    ):
        validate_resume_match_result(result, requirements)


def test_langgraph_retries_invalid_result_and_passes_feedback():
    requirements = make_requirements("Python", "Docker")
    invalid_result = ResumeMatchResult(matches=[make_match("Python")])
    valid_result = ResumeMatchResult(
        matches=[make_match("Python"), make_match("Docker")]
    )

    with patch(
        "backend.services.ai_service._generate_resume_match_result",
        side_effect=[invalid_result, valid_result],
    ) as mock_generate:
        state = run_resume_matching_workflow("Resume text", requirements)

    assert state["match_result"] == valid_result
    assert state["attempt_count"] == 2
    assert state["retries_exhausted"] is False
    assert mock_generate.call_count == 2
    assert mock_generate.call_args_list[0].kwargs["validation_feedback"] is None
    assert mock_generate.call_args_list[1].kwargs["validation_feedback"] == (
        "Missing matches for requirements: ['Docker']."
    )


def test_validation_feedback_is_included_in_retry_prompt():
    requirements = make_requirements("Python")
    generated_result = ResumeMatchResult(matches=[make_match("Python")])

    with patch(
        "backend.services.ai_service.client.responses.parse",
        return_value=SimpleNamespace(output_parsed=generated_result),
    ) as mock_parse:
        from backend.services.ai_service import _generate_resume_match_result

        _generate_resume_match_result(
            "Resume text",
            requirements,
            validation_feedback="Unknown matches: ['Docker'].",
        )

    user_prompt = mock_parse.call_args.kwargs["input"][1]["content"]
    system_prompt = mock_parse.call_args.kwargs["input"][0]["content"]
    assert mock_parse.call_args.kwargs["model"] == MODEL_NAME
    assert system_prompt == MATCH_V3_SYSTEM_PROMPT
    assert "A previous match result failed validation." in user_prompt
    assert "Validation error: Unknown matches: ['Docker']." in user_prompt


def test_explicit_evaluation_prompt_does_not_change_production_default():
    requirements = make_requirements("Python")
    generated_result = ResumeMatchResult(matches=[make_match("Python")])

    with patch(
        "backend.services.ai_service.client.responses.parse",
        return_value=SimpleNamespace(output_parsed=generated_result),
    ) as mock_parse:
        from backend.services.ai_service import _generate_resume_match_result

        _generate_resume_match_result(
            "Resume text",
            requirements,
            prompt_version="match-v1",
        )

    assert mock_parse.call_args.kwargs["input"][0]["content"] == (
        MATCH_V1_SYSTEM_PROMPT
    )
    assert MATCH_PROMPT_VERSION == "match-v3"


def test_matching_workflow_passes_explicit_prompt_through_retries():
    requirements = make_requirements("Python", "Docker")
    invalid_result = ResumeMatchResult(matches=[make_match("Python")])
    valid_result = ResumeMatchResult(
        matches=[make_match("Python"), make_match("Docker")]
    )

    with patch(
        "backend.services.ai_service._generate_resume_match_result",
        side_effect=[invalid_result, valid_result],
    ) as mock_generate:
        state = run_resume_matching_workflow(
            "Resume text",
            requirements,
            prompt_version="match-v2",
        )

    assert state["match_result"] == valid_result
    assert state["attempt_count"] == 2
    assert all(
        call.kwargs["prompt_version"] == "match-v2"
        for call in mock_generate.call_args_list
    )


def test_historical_prompts_are_preserved_while_match_v3_is_active():
    assert MATCH_PROMPT_VERSION == "match-v3"
    assert MATCH_SYSTEM_PROMPTS["match-v1"] == MATCH_V1_SYSTEM_PROMPT
    assert MATCH_SYSTEM_PROMPTS["match-v2"] == MATCH_V2_SYSTEM_PROMPT
    assert MATCH_SYSTEM_PROMPTS["match-v3"] == MATCH_V3_SYSTEM_PROMPT
    assert len(
        {MATCH_V1_SYSTEM_PROMPT, MATCH_V2_SYSTEM_PROMPT, MATCH_V3_SYSTEM_PROMPT}
    ) == 3
    assert "not_assessable" not in MATCH_V1_SYSTEM_PROMPT
    assert "not_assessable" not in MATCH_V2_SYSTEM_PROMPT
    assert "not_assessable" in MATCH_V3_SYSTEM_PROMPT


def test_langgraph_returns_valid_result_without_retry():
    requirements = make_requirements("Python")
    valid_result = ResumeMatchResult(matches=[make_match("Python")])

    with patch(
        "backend.services.ai_service._generate_resume_match_result",
        return_value=valid_result,
    ) as mock_generate:
        result = match_resume_to_requirements("Resume text", requirements)

    assert result == valid_result
    assert mock_generate.call_count == 1


def test_state_runner_exposes_first_attempt_success():
    requirements = make_requirements("Python")
    valid_result = ResumeMatchResult(matches=[make_match("Python")])

    with patch(
        "backend.services.ai_service._generate_resume_match_result",
        return_value=valid_result,
    ):
        state = run_resume_matching_workflow("Resume text", requirements)

    assert state["match_result"] == valid_result
    assert state["attempt_count"] == 1
    assert state["retries_exhausted"] is False


def test_state_runner_marks_retry_exhaustion_without_raising():
    requirements = make_requirements("Python", "Docker")
    invalid_result = ResumeMatchResult(matches=[make_match("Python")])

    with patch(
        "backend.services.ai_service._generate_resume_match_result",
        return_value=invalid_result,
    ) as mock_generate:
        state = run_resume_matching_workflow("Resume text", requirements)

    assert state["match_result"] == invalid_result
    assert state["attempt_count"] == 3
    assert state["retries_exhausted"] is True
    assert mock_generate.call_count == 3


def test_langgraph_retry_exhaustion_raises_after_three_generation_attempts():
    requirements = make_requirements("Python", "Docker")
    invalid_result = ResumeMatchResult(matches=[make_match("Python")])

    with patch(
        "backend.services.ai_service._generate_resume_match_result",
        return_value=invalid_result,
    ) as mock_generate:
        with pytest.raises(ValueError, match="after 3 attempts"):
            match_resume_to_requirements(
                "Resume text",
                requirements,
            )

    assert mock_generate.call_count == 3
