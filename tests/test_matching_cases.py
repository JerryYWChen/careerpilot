from backend.evals.matching_cases import MATCHING_EVAL_CASES


NEW_CASE_NAMES = [
    "Next.js Does Not Reliably Establish TypeScript",
    "Container Experience Without Orchestration",
    "Compound AND Requirement Partially Satisfied",
    "Compound OR Requirement Satisfied",
    "AWS Platform and Lambda Are Separate Requirements",
    "Experience Exactly Meets Minimum",
    "Overlapping Experience Does Not Add Linearly",
    "Leadership Signals Without People Management",
]


def test_matching_evaluation_dataset_contains_new_cases():
    assert len(MATCHING_EVAL_CASES) == 17
    assert [case.name for case in MATCHING_EVAL_CASES[-8:]] == NEW_CASE_NAMES


def test_new_cases_define_expectations_for_every_requirement():
    for case in MATCHING_EVAL_CASES[-8:]:
        requirement_names = {
            requirement.name
            for requirement in case.job_requirements.requirements
        }

        assert set(case.expected_matches) == requirement_names
        assert case.policy_rationale
