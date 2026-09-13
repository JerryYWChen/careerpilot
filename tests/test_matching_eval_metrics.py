import pytest

from backend.evals.run_matching_eval import calculate_evaluation_metrics


def test_calculates_coverage_repair_exhaustion_and_semantic_metrics():
    runs = [
        {"attempt_count": 1, "retries_exhausted": False, "semantic_passed": True},
        {"attempt_count": 2, "retries_exhausted": False, "semantic_passed": True},
        {"attempt_count": 3, "retries_exhausted": False, "semantic_passed": False},
        {"attempt_count": 3, "retries_exhausted": True, "semantic_passed": False},
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
    assert metrics["semantic_pass_count"] == 2
    assert metrics["semantic_accuracy_percent"] == 50.0


def test_repair_recovery_rate_is_none_without_repair_opportunities():
    metrics = calculate_evaluation_metrics(
        [
            {
                "attempt_count": 1,
                "retries_exhausted": False,
                "semantic_passed": True,
            }
        ]
    )

    assert metrics["repair_opportunity_count"] == 0
    assert metrics["repair_recovery_percent"] is None
