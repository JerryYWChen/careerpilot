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

test_matches = ResumeMatchResult(
    matches=[
        RequirementMatch(
            requirement_name="Python",
            status="matched",
            evidence="Built backend APIs using Python.",
            reason="The resume demonstrates practical Python experience."
        ),
        RequirementMatch(
            requirement_name="AWS",
            status="partial",
            evidence="AWS is listed in the Skills section.",
            reason="AWS is mentioned but practical experience is not demonstrated."
        ),
        RequirementMatch(
            requirement_name="Docker",
            status="missing",
            evidence=None,
            reason="Docker is not mentioned in the resume."
        )
    ]
)

analysis = build_match_analysis(test_matches)

print(analysis)
