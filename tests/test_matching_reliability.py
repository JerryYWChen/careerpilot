from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.models.analysis import (
    JobRequirements,
    MatchStatus,
    Requirement,
    RequirementMatch,
    ResumeMatchResult,
)
from backend.services.ai_service import match_resume_to_requirements
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


def test_invalid_result_retries_and_passes_feedback_to_next_attempt():
    requirements = make_requirements("Python", "Docker")
    invalid_result = ResumeMatchResult(matches=[make_match("Python")])
    valid_result = ResumeMatchResult(
        matches=[make_match("Python"), make_match("Docker")]
    )

    with patch(
        "backend.services.ai_service._generate_resume_match_result",
        side_effect=[invalid_result, valid_result],
    ) as mock_generate:
        result = match_resume_to_requirements("Resume text", requirements)

    assert result == valid_result
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
    assert "A previous match result failed validation." in user_prompt
    assert "Validation error: Unknown matches: ['Docker']." in user_prompt


def test_valid_result_returns_without_retry():
    requirements = make_requirements("Python")
    valid_result = ResumeMatchResult(matches=[make_match("Python")])

    with patch(
        "backend.services.ai_service._generate_resume_match_result",
        return_value=valid_result,
    ) as mock_generate:
        result = match_resume_to_requirements("Resume text", requirements)

    assert result == valid_result
    assert mock_generate.call_count == 1


def test_retry_exhaustion_raises_after_three_generation_attempts():
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
