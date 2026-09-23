from unittest.mock import patch

import pytest

from backend.agents.matching_graph import run_resume_matching_workflow
from backend.evals.matching_cases import MATCHING_EVAL_CASES
from backend.models.analysis import (
    EvidenceSource,
    JobRequirements,
    MatchStatus,
    Requirement,
    RequirementMatch,
    ResumeMatchResult,
)
from backend.models.api import AnalyzeResponse
from backend.rag.planning_context import retrieve_planning_context
from backend.services.planner_service import create_validated_career_action_plan
from backend.services.scoring_service import (
    build_match_analysis,
    calculate_match_score,
    validate_resume_match_result,
)


def _requirements(*requirements: Requirement) -> JobRequirements:
    return JobRequirements(
        job_title="Software Engineer",
        seniority_level="unknown",
        summary="Test requirements.",
        requirements=list(requirements),
    )


def _requirement(
    name: str,
    *,
    importance: str = "required",
) -> Requirement:
    return Requirement(
        name=name,
        category="skill",
        importance=importance,
    )


def _match(
    name: str,
    status: MatchStatus,
    *,
    evidence: str | None = None,
    sources: list[EvidenceSource] | None = None,
    reason: str | None = None,
) -> RequirementMatch:
    return RequirementMatch(
        requirement_name=name,
        status=status,
        evidence=evidence,
        evidence_sources=sources or [],
        reason=reason or "No reliable resume evidence was identified.",
    )


def test_not_assessable_is_excluded_from_both_sides_of_score():
    requirements = _requirements(
        _requirement("Python"),
        _requirement("Docker", importance="preferred"),
        _requirement("Strong communication skills"),
    )
    result = ResumeMatchResult(
        matches=[
            _match(
                "Python",
                MatchStatus.MATCHED,
                evidence="Built Python APIs.",
                sources=[EvidenceSource.EXPERIENCE],
            ),
            _match("Docker", MatchStatus.MISSING),
            _match(
                "Strong communication skills",
                MatchStatus.NOT_ASSESSABLE,
                reason=(
                    "Resume evidence is insufficient to reliably assess this "
                    "generic capability."
                ),
            ),
        ]
    )

    assert calculate_match_score(result, requirements) == 75.0


def test_all_not_assessable_current_float_contract_returns_zero():
    """Documents the non-nullable score limitation until the API can represent N/A."""
    requirements = _requirements(_requirement("Strong communication skills"))
    result = ResumeMatchResult(
        matches=[
            _match(
                "Strong communication skills",
                MatchStatus.NOT_ASSESSABLE,
                reason=(
                    "The resume does not provide evidence that can reliably assess "
                    "this generic capability."
                ),
            )
        ]
    )

    assert calculate_match_score(result, requirements) == 0.0


def test_match_analysis_separates_not_assessable_from_strengths_and_gaps():
    result = ResumeMatchResult(
        matches=[
            _match(
                "Python",
                MatchStatus.MATCHED,
                evidence="Built Python APIs.",
                sources=[EvidenceSource.EXPERIENCE],
            ),
            _match("AWS", MatchStatus.MISSING),
            _match(
                "Strong communication skills",
                MatchStatus.NOT_ASSESSABLE,
                reason=(
                    "Resume evidence is insufficient to reliably assess this "
                    "generic capability."
                ),
            ),
        ]
    )

    analysis = build_match_analysis(result)

    assert [item.area for item in analysis.strengths] == ["Python"]
    assert [item.area for item in analysis.gaps] == ["AWS"]
    assert [item.area for item in analysis.not_assessable] == [
        "Strong communication skills"
    ]
    assert analysis.not_assessable[0].status == MatchStatus.NOT_ASSESSABLE


@pytest.mark.parametrize("status", [MatchStatus.MATCHED, MatchStatus.PARTIAL])
def test_positive_statuses_require_evidence_and_sources(status):
    requirements = _requirements(_requirement("Python"))
    result = ResumeMatchResult(matches=[_match("Python", status)])

    with pytest.raises(ValueError, match="must include positive resume evidence"):
        validate_resume_match_result(result, requirements)


@pytest.mark.parametrize(
    "status",
    [MatchStatus.MISSING, MatchStatus.NOT_ASSESSABLE],
)
def test_negative_or_unassessable_statuses_reject_positive_evidence(status):
    requirements = _requirements(_requirement("Communication"))
    result = ResumeMatchResult(
        matches=[
            _match(
                "Communication",
                status,
                evidence="Presented project results.",
                sources=[EvidenceSource.EXPERIENCE],
                reason=(
                    "Resume evidence is insufficient to reliably assess the full "
                    "requirement."
                ),
            )
        ]
    )

    with pytest.raises(ValueError, match="must not claim positive resume evidence"):
        validate_resume_match_result(result, requirements)


def test_not_assessable_reason_must_describe_evidence_limitation():
    requirements = _requirements(_requirement("Communication"))
    result = ResumeMatchResult(
        matches=[
            _match(
                "Communication",
                MatchStatus.NOT_ASSESSABLE,
                reason="The candidate lacks communication skills.",
            )
        ]
    )

    with pytest.raises(ValueError) as error:
        validate_resume_match_result(result, requirements)

    assert "must describe the limitation" in str(error.value)
    assert "must not claim that the candidate lacks" in str(error.value)


def test_not_assessable_validation_failure_uses_existing_bounded_retry():
    requirements = _requirements(_requirement("Communication"))
    invalid = ResumeMatchResult(
        matches=[
            _match(
                "Communication",
                MatchStatus.NOT_ASSESSABLE,
                reason="The candidate lacks communication skills.",
            )
        ]
    )
    valid = ResumeMatchResult(
        matches=[
            _match(
                "Communication",
                MatchStatus.NOT_ASSESSABLE,
                reason=(
                    "The resume does not provide evidence that can reliably assess "
                    "this generic capability."
                ),
            )
        ]
    )

    with patch(
        "backend.services.ai_service._generate_resume_match_result",
        side_effect=[invalid, valid],
    ) as generate:
        state = run_resume_matching_workflow("Resume text", requirements)

    assert state["match_result"] == valid
    assert state["attempt_count"] == 2
    assert generate.call_args_list[1].kwargs["validation_feedback"] is not None


def test_not_assessable_items_do_not_reach_planning_or_rag():
    analysis = build_match_analysis(
        ResumeMatchResult(
            matches=[
                _match(
                    "Strong communication skills",
                    MatchStatus.NOT_ASSESSABLE,
                    reason=(
                        "Resume evidence is insufficient to reliably assess this "
                        "generic capability."
                    ),
                )
            ]
        )
    )

    with patch("backend.rag.planning_context.retrieve_chunks") as retrieve:
        assert retrieve_planning_context(analysis.gaps) == []
    retrieve.assert_not_called()

    with (
        patch("backend.services.planner_service.retrieve_planning_context") as context,
        patch("backend.services.planner_service.generate_career_action_plan") as plan,
    ):
        result = create_validated_career_action_plan(analysis.gaps)

    assert result.actions == []
    context.assert_not_called()
    plan.assert_not_called()


def test_api_schema_exposes_not_assessable_collection():
    assert "not_assessable" in AnalyzeResponse.model_fields


def test_semantic_regression_cases_define_the_requested_boundary():
    expected = {
        "Effective Verbal and Written Communication Is Not Assessable": (
            "Effective verbal and written communication skills",
            MatchStatus.NOT_ASSESSABLE,
        ),
        "Generic Cross-Functional Collaboration Is Not Assessable": (
            "Ability to collaborate cross-functionally",
            MatchStatus.NOT_ASSESSABLE,
        ),
        "Concrete Product and Design Collaboration Is Missing": (
            "Experience partnering with Product and Design to deliver launches",
            MatchStatus.MISSING,
        ),
        "Validation and Debugging Do Not Establish High Attention to Detail": (
            "High attention to detail",
            MatchStatus.NOT_ASSESSABLE,
        ),
        "Broad Software Work Does Not Establish Attention to Detail": (
            "Attention to detail",
            MatchStatus.NOT_ASSESSABLE,
        ),
        "Documentation Does Not Establish Excellent Communication Quality": (
            "Excellent written and verbal communication",
            MatchStatus.NOT_ASSESSABLE,
        ),
        "Executive Presentation Is Directly Demonstrated": (
            "Presented technical results to executives",
            MatchStatus.MATCHED,
        ),
        "Leadership Scope Is Directly Demonstrated": (
            "Led a team of 5 engineers",
            MatchStatus.MATCHED,
        ),
        "Azure and Python Do Not Establish AWS": (
            "AWS experience",
            MatchStatus.MISSING,
        ),
        "Multitasking Effectiveness Is Not Assessable": (
            "Ability to manage multiple tasks effectively",
            MatchStatus.NOT_ASSESSABLE,
        ),
        "Cross-Functional Activity Does Not Establish Strong Collaboration": (
            "Strong collaboration skills",
            MatchStatus.NOT_ASSESSABLE,
        ),
        "Product and Design Collaboration Experience Is Demonstrated": (
            "Experience collaborating with Product and Design",
            MatchStatus.MATCHED,
        ),
        "Technical Documentation Experience Is Demonstrated": (
            "Experience producing technical documentation",
            MatchStatus.MATCHED,
        ),
        "Developer Tooling Capability Remains Resume Assessable": (
            "Ability to build and debug personal developer tooling",
            MatchStatus.MATCHED,
        ),
        "Hardware and Switch Experience Remains Resume Assessable": (
            "Hands-on experience racking machines, running cable, and configuring switches",
            MatchStatus.MISSING,
        ),
        "Onsite Internship Availability Remains Not Assessable": (
            "Ability to work on-site in Azusa for the full internship",
            MatchStatus.NOT_ASSESSABLE,
        ),
    }
    cases = {case.name: case for case in MATCHING_EVAL_CASES}

    for case_name, (requirement_name, status) in expected.items():
        assert cases[case_name].expected_matches[requirement_name].status == status
