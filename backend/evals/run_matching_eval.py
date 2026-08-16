from backend.evals.matching_cases import MATCHING_EVAL_CASES
from backend.services.ai_service import match_resume_to_requirements


RUNS_PER_CASE = 3


def find_actual_match(requirement_name, actual_result):
    for match in actual_result.matches:
        if match.requirement_name.lower() == requirement_name.lower():
            return match

    return None


summary = []


for case in MATCHING_EVAL_CASES:
    print(f"\n=== {case.name} ===")

    case_passes = 0

    for run in range(1, RUNS_PER_CASE + 1):
        actual_result = match_resume_to_requirements(
            case.resume_text,
            case.job_requirements
        )

        passed = 0
        total = len(case.expected_matches)

        for requirement_name, expected_match in case.expected_matches.items():
            actual_match = find_actual_match(
                requirement_name,
                actual_result
            )

            if actual_match is None:
                print(f"  FAIL: {requirement_name}")
                print(f"    expected status: {expected_match.status.value}")
                print("    actual: no match returned")
                continue

            status_matches = (
                actual_match.status == expected_match.status
            )

            sources_match = (
                expected_match.evidence_sources is None
                or set(actual_match.evidence_sources)
                == set(expected_match.evidence_sources)
            )

            if status_matches and sources_match:
                passed += 1

            else:
                print(f"  FAIL: {requirement_name}")

                if not status_matches:
                    print(
                        f"    expected status: "
                        f"{expected_match.status.value}"
                    )
                    print(
                        f"    actual status:   "
                        f"{actual_match.status.value}"
                    )

                if not sources_match:
                    print(
                        f"    expected sources: "
                        f"{expected_match.evidence_sources}"
                    )
                    print(
                        f"    actual sources:   "
                        f"{actual_match.evidence_sources}"
                    )

                print(f"    evidence: {actual_match.evidence}")
                print(f"    reason:   {actual_match.reason}")
        # for requirement_name, expected_match in case.expected_matches.items():
        #     actual_match = find_actual_match(
        #         requirement_name,
        #         actual_result
        #     )
        #     print(actual_result)

        #     if actual_match is None:
        #         print(f"  FAIL: {requirement_name}")
        #         print(f"    expected: {expected_match.status.value}")
        #         print("    actual:   no match returned")

        #     elif actual_match.status == expected_match.status:
        #         passed += 1

        #     else:
        #         print(f"  FAIL: {requirement_name}")
        #         print(f"    expected: {expected_match.status.value}")
        #         print(f"    actual:   {actual_match.status.value}")
        #         print(f"    evidence: {actual_match.evidence}")
        #         print(f"    reason:   {actual_match.reason}")

        if passed == total:
            case_passes += 1
            print(f"Run {run}: PASS")
        else:
            print(f"Run {run}: FAIL")

    consistency = case_passes / RUNS_PER_CASE * 100

    print(
        f"Consistency: {case_passes}/{RUNS_PER_CASE} "
        f"({consistency:.0f}%)"
    )

    summary.append(
        {
            "name": case.name,
            "passes": case_passes,
            "runs": RUNS_PER_CASE,
            "consistency": consistency,
        }
    )


print("\n=== Evaluation Summary ===")

for result in summary:
    print(
        f"{result['name']}: "
        f"{result['passes']}/{result['runs']} "
        f"({result['consistency']:.0f}%)"
    )


total_passes = sum(
    result["passes"]
    for result in summary
)

total_runs = len(summary) * RUNS_PER_CASE

overall_accuracy = total_passes / total_runs * 100

print(
    f"\nOverall Run Accuracy: "
    f"{total_passes}/{total_runs} "
    f"({overall_accuracy:.1f}%)"
)

