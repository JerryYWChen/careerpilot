from backend.agents.matching_graph import run_resume_matching_workflow
from backend.evals.matching_cases import MATCHING_EVAL_CASES
from backend.services.ai_service import MATCH_PROMPT_VERSION, MODEL_NAME


RUNS_PER_CASE = 3


def find_actual_match(requirement_name, actual_result):
    for match in actual_result.matches:
        if match.requirement_name.lower() == requirement_name.lower():
            return match

    return None


def calculate_evaluation_metrics(run_results: list[dict]) -> dict:
    total_runs = len(run_results)

    def percentage(count: int, total: int) -> float:
        if total == 0:
            return 0.0
        return round(count / total * 100, 2)

    pass_at_1 = sum(
        not result["retries_exhausted"]
        and result["attempt_count"] == 1
        for result in run_results
    )
    pass_at_3 = sum(
        not result["retries_exhausted"]
        for result in run_results
    )
    repair_opportunities = total_runs - pass_at_1
    repair_recoveries = sum(
        not result["retries_exhausted"]
        and result["attempt_count"] > 1
        for result in run_results
    )
    retry_exhaustions = sum(
        result["retries_exhausted"]
        for result in run_results
    )
    semantic_passes = sum(
        result["semantic_passed"]
        for result in run_results
    )

    recovery_percent = None
    if repair_opportunities:
        recovery_percent = percentage(
            repair_recoveries,
            repair_opportunities,
        )

    return {
        "total_runs": total_runs,
        "coverage_pass_at_1_count": pass_at_1,
        "coverage_pass_at_1_percent": percentage(pass_at_1, total_runs),
        "coverage_pass_at_3_count": pass_at_3,
        "coverage_pass_at_3_percent": percentage(pass_at_3, total_runs),
        "repair_opportunity_count": repair_opportunities,
        "repair_recovery_count": repair_recoveries,
        "repair_recovery_percent": recovery_percent,
        "retry_exhaustion_count": retry_exhaustions,
        "retry_exhaustion_percent": percentage(retry_exhaustions, total_runs),
        "semantic_pass_count": semantic_passes,
        "semantic_accuracy_percent": percentage(semantic_passes, total_runs),
    }


def evaluate_semantic_result(case, actual_result) -> bool:
    passed = 0

    for requirement_name, expected_match in case.expected_matches.items():
        actual_match = find_actual_match(requirement_name, actual_result)

        if actual_match is None:
            print(f"  FAIL: {requirement_name}")
            print(f"    expected status: {expected_match.status.value}")
            print("    actual: no match returned")
            continue

        status_matches = actual_match.status == expected_match.status
        sources_match = (
            expected_match.evidence_sources is None
            or set(actual_match.evidence_sources)
            == set(expected_match.evidence_sources)
        )

        if status_matches and sources_match:
            passed += 1
            continue

        print(f"  FAIL: {requirement_name}")

        if not status_matches:
            print(f"    expected status: {expected_match.status.value}")
            print(f"    actual status:   {actual_match.status.value}")

        if not sources_match:
            print(f"    expected sources: {expected_match.evidence_sources}")
            print(f"    actual sources:   {actual_match.evidence_sources}")

        print(f"    evidence: {actual_match.evidence}")
        print(f"    reason:   {actual_match.reason}")

    return passed == len(case.expected_matches)


def format_metric(count: int, total: int, percent: float | None) -> str:
    if percent is None:
        return f"{count}/{total} (N/A)"
    return f"{count}/{total} ({percent:.1f}%)"


def main():
    case_summary = []
    run_results = []

    print(f"Model: {MODEL_NAME}")
    print(f"Match prompt: {MATCH_PROMPT_VERSION}")

    for case in MATCHING_EVAL_CASES:
        print(f"\n=== {case.name} ===")
        case_passes = 0

        for run in range(1, RUNS_PER_CASE + 1):
            state = run_resume_matching_workflow(
                case.resume_text,
                case.job_requirements,
            )
            attempt_count = state["attempt_count"]
            exhausted = state["retries_exhausted"]

            if exhausted:
                print(f"Run {run} coverage: EXHAUSTED@{attempt_count}")
                semantic_passed = False
            else:
                if attempt_count == 1:
                    coverage_result = "PASS@1"
                else:
                    coverage_result = f"RECOVERED@{attempt_count}"

                print(f"Run {run} coverage: {coverage_result}")
                semantic_passed = evaluate_semantic_result(
                    case,
                    state["match_result"],
                )

            if semantic_passed:
                case_passes += 1
                print(f"Run {run} semantic result: PASS")
            else:
                print(f"Run {run} semantic result: FAIL")

            run_results.append(
                {
                    "attempt_count": attempt_count,
                    "retries_exhausted": exhausted,
                    "semantic_passed": semantic_passed,
                }
            )

        consistency = case_passes / RUNS_PER_CASE * 100
        print(
            f"Semantic consistency: {case_passes}/{RUNS_PER_CASE} "
            f"({consistency:.0f}%)"
        )
        case_summary.append(
            {
                "name": case.name,
                "passes": case_passes,
                "runs": RUNS_PER_CASE,
                "consistency": consistency,
            }
        )

    print("\n=== Evaluation Summary ===")

    for result in case_summary:
        print(
            f"{result['name']}: "
            f"{result['passes']}/{result['runs']} "
            f"({result['consistency']:.0f}%)"
        )

    metrics = calculate_evaluation_metrics(run_results)
    total_runs = metrics["total_runs"]

    print(
        "\nCoverage pass@1: "
        + format_metric(
            metrics["coverage_pass_at_1_count"],
            total_runs,
            metrics["coverage_pass_at_1_percent"],
        )
    )
    print(
        "Coverage pass@3: "
        + format_metric(
            metrics["coverage_pass_at_3_count"],
            total_runs,
            metrics["coverage_pass_at_3_percent"],
        )
    )
    print(
        "Repair recovery: "
        + format_metric(
            metrics["repair_recovery_count"],
            metrics["repair_opportunity_count"],
            metrics["repair_recovery_percent"],
        )
    )
    print(
        "Retry exhaustion: "
        + format_metric(
            metrics["retry_exhaustion_count"],
            total_runs,
            metrics["retry_exhaustion_percent"],
        )
    )
    print(
        "Final semantic accuracy: "
        + format_metric(
            metrics["semantic_pass_count"],
            total_runs,
            metrics["semantic_accuracy_percent"],
        )
    )


if __name__ == "__main__":
    main()
