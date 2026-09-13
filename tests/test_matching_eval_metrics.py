import pytest

from backend.evals.run_matching_eval import (
    calculate_evaluation_metrics,
    evaluate_semantic_result,
)
from backend.models.analysis import (
    EvidenceSource,
    MatchStatus,
    RequirementMatch,
    ResumeMatchResult,
)


def test_calculates_coverage_and_separate_semantic_metrics():
    runs = [
        {
            "attempt_count": 1,
            "retries_exhausted": False,
            "status_passed": True,
            "evidence_sources_passed": True,
        },
        {
            "attempt_count": 2,
            "retries_exhausted": False,
            "status_passed": True,
            "evidence_sources_passed": True,
        },
        {
            "attempt_count": 3,
            "retries_exhausted": False,
            "status_passed": False,
            "evidence_sources_passed": True,
        },
        {
            "attempt_count": 3,
            "retries_exhausted": True,
            "status_passed": True,
            "evidence_sources_passed": False,
        },
    ]

    metrics = calculate_evaluation_metrics(runs)

    assert metrics["total_runs"] == 4
    assert metrics["coverage_pass_at_1_count"] == 1
    assert metrics["coverage_pass_at_1_percent"] == 25.0
    assert metrics["coverage_pass_at_3_count"] == 3
    assert metrics["coverage_pass_at_3_percent"] == 75.0
    assert metrics["repair_opportunity_count"] == 3
    assert metrics["repair_recovery_count"] == 2
    assert metrics["repair_recovery_percent"] == pytest.approx(66.67)
    assert metrics["retry_exhaustion_count"] == 1
    assert metrics["retry_exhaustion_percent"] == 25.0
    assert metrics["status_pass_count"] == 3
    assert metrics["status_accuracy_percent"] == 75.0
    assert metrics["evidence_source_pass_count"] == 3
    assert metrics["evidence_source_accuracy_percent"] == 75.0
    assert metrics["strict_semantic_pass_count"] == 2
    assert metrics["strict_semantic_accuracy_percent"] == 50.0


def test_repair_recovery_rate_is_none_without_repair_opportunities():
    metrics = calculate_evaluation_metrics(
        [
            {
                "attempt_count": 1,
                "retries_exhausted": False,
                "status_passed": True,
                "evidence_sources_passed": True,
            }
        ]
    )

    assert metrics["repair_opportunity_count"] == 0
    assert metrics["repair_recovery_percent"] is None


def test_semantic_evaluation_separates_status_and_evidence_sources():
    class ExpectedMatch:
        status = MatchStatus.MATCHED
        evidence_sources = [EvidenceSource.SKILLS]

    class EvalCase:
        expected_matches = {"Python": ExpectedMatch()}

    actual_result = ResumeMatchResult(
        matches=[
            RequirementMatch(
                requirement_name="Python",
                status=MatchStatus.MATCHED,
                evidence="Built Python APIs.",
                evidence_sources=[EvidenceSource.EXPERIENCE],
                reason="Python is demonstrated in experience.",
            )
        ]
    )

    status_passed, evidence_sources_passed = evaluate_semantic_result(
        EvalCase(),
        actual_result,
    )

    assert status_passed is True
    assert evidence_sources_passed is False
