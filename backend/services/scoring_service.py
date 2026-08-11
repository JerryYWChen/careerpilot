from backend.models.analysis import (
    JobRequirements,
    MatchStatus,
    Requirement,
    RequirementImportance,
    RequirementMatch,
    ResumeMatchResult,
)

MATCH_VALUES = {
    MatchStatus.MATCHED: 1.0,
    MatchStatus.PARTIAL: 0.8,
    MatchStatus.MISSING: 0.0,
}

IMPORTANCE_WEIGHTS = {
    RequirementImportance.REQUIRED: 3,
    RequirementImportance.PREFERRED: 1,
}

def find_match(
    requirement: Requirement,
    match_result: ResumeMatchResult
) -> RequirementMatch:
    for match in match_result.matches:
        if match.requirement_name.lower() == requirement.name.lower():
            return match

    raise ValueError(
        f"Match not found for requirement: {requirement.name}"
    )


def calculate_match_score(
    match_result: ResumeMatchResult,
    requirements: JobRequirements
) -> float:
    earned_score = 0.0
    maximum_score = 0.0

    for requirement in requirements.requirements:
        match = find_match(requirement, match_result)

        match_value = MATCH_VALUES[match.status]
        importance_weight = IMPORTANCE_WEIGHTS[requirement.importance]

        earned_score += match_value * importance_weight
        maximum_score += importance_weight

    if maximum_score == 0:
        return 0.0

    return round(
        earned_score / maximum_score * 100,
        2
    )

