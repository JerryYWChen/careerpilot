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

NOT_ASSESSABLE_CASE_NAMES = [
    "Effective Verbal and Written Communication Is Not Assessable",
    "Generic Cross-Functional Collaboration Is Not Assessable",
    "Concrete Product and Design Collaboration Is Missing",
    "Validation and Debugging Do Not Establish High Attention to Detail",
    "Broad Software Work Does Not Establish Attention to Detail",
    "Documentation Does Not Establish Excellent Communication Quality",
    "Executive Presentation Is Directly Demonstrated",
    "Leadership Scope Is Directly Demonstrated",
    "Azure and Python Do Not Establish AWS",
    "Multitasking Effectiveness Is Not Assessable",
    "Cross-Functional Activity Does Not Establish Strong Collaboration",
    "Product and Design Collaboration Experience Is Demonstrated",
    "Technical Documentation Experience Is Demonstrated",
    "Developer Tooling Capability Remains Resume Assessable",
    "Hardware and Switch Experience Remains Resume Assessable",
    "Onsite Internship Availability Remains Not Assessable",
]


def test_matching_evaluation_dataset_contains_new_cases():
    assert len(MATCHING_EVAL_CASES) == 33
    assert [case.name for case in MATCHING_EVAL_CASES[9:17]] == NEW_CASE_NAMES
    assert [case.name for case in MATCHING_EVAL_CASES[-16:]] == (
        NOT_ASSESSABLE_CASE_NAMES
    )


def test_new_cases_define_expectations_for_every_requirement():
    for case in MATCHING_EVAL_CASES[9:]:
        requirement_names = {
            requirement.name
            for requirement in case.job_requirements.requirements
        }

        assert set(case.expected_matches) == requirement_names
        assert case.policy_rationale
