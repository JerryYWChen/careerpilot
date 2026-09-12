from backend.models.analysis import (
    Gap,
    JobRequirements,
    MatchAnalysis,
    MatchStatus,
    Requirement,
    RequirementImportance,
    RequirementMatch,
    ResumeMatchResult,
    Strength,
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

def validate_resume_match_result(
    match_result: ResumeMatchResult,
    requirements: JobRequirements,
) -> None:
    expected_names = {
        requirement.name.lower(): requirement.name
        for requirement in requirements.requirements
    }
    actual_name_counts: dict[str, int] = {}
    actual_names: dict[str, str] = {}

    for match in match_result.matches:
        normalized_name = match.requirement_name.lower()
        actual_name_counts[normalized_name] = (
            actual_name_counts.get(normalized_name, 0) + 1
        )
        actual_names.setdefault(normalized_name, match.requirement_name)

    missing = sorted(
        original_name
        for normalized_name, original_name in expected_names.items()
        if normalized_name not in actual_name_counts
    )
    duplicates = sorted(
        actual_names[normalized_name]
        for normalized_name, count in actual_name_counts.items()
        if count > 1
    )
    unknown = sorted(
        actual_names[normalized_name]
        for normalized_name in actual_name_counts
        if normalized_name not in expected_names
    )

    errors = []

    if missing:
        errors.append(f"Missing matches for requirements: {missing}.")

    if duplicates:
        errors.append(f"Duplicate matches for requirements: {duplicates}.")

    if unknown:
        errors.append(f"Unknown matches: {unknown}.")

    if errors:
        raise ValueError(" ".join(errors))

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

def build_match_analysis(match_result: ResumeMatchResult) -> MatchAnalysis:
    strengths = []
    gaps = []

    for match in match_result.matches:
        if match.status == MatchStatus.MATCHED:
            strengths.append(
                Strength(
                    area=match.requirement_name,
                    evidence=match.evidence,
                    reason=match.reason
                )
            )
        else:
            gaps.append(
                Gap(
                    area=match.requirement_name,
                    status=match.status,
                    evidence=match.evidence,
                    reason=match.reason
                )
            )

    return MatchAnalysis(
        strengths=strengths,
        gaps=gaps
    )

