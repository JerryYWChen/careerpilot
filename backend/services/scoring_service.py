import re

from backend.models.analysis import (
    Gap,
    JobRequirements,
    MatchAnalysis,
    MatchStatus,
    NotAssessableRequirement,
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

_EVIDENCE_LIMITATION_LANGUAGE = re.compile(
    r"\b(resume|evidence)\b.*\b(assess|assessable|evaluate|establish|"
    r"demonstrate|determine|insufficient|reliably)\b|"
    r"\b(assess|assessable|evaluate|establish|demonstrate|determine|"
    r"insufficient|reliably)\b.*\b(resume|evidence)\b",
    flags=re.IGNORECASE,
)
_UNSUPPORTED_CAPABILITY_ABSENCE = re.compile(
    r"\b(?:candidate|applicant)\s+(?:lacks|does not have|doesn't have|"
    r"has no|is unable to)\b",
    flags=re.IGNORECASE,
)

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

    for match in match_result.matches:
        has_evidence = bool(match.evidence and match.evidence.strip())
        has_sources = bool(match.evidence_sources)

        if match.status in {MatchStatus.MATCHED, MatchStatus.PARTIAL}:
            if not has_evidence or not has_sources:
                errors.append(
                    f"{match.status.value} match for '{match.requirement_name}' "
                    "must include positive resume evidence and evidence sources."
                )

        if match.status in {
            MatchStatus.MISSING,
            MatchStatus.NOT_ASSESSABLE,
        } and (has_evidence or has_sources):
            errors.append(
                f"{match.status.value} match for '{match.requirement_name}' "
                "must not claim positive resume evidence or evidence sources."
            )

        if match.status == MatchStatus.NOT_ASSESSABLE:
            if not _EVIDENCE_LIMITATION_LANGUAGE.search(match.reason):
                errors.append(
                    f"not_assessable reason for '{match.requirement_name}' must "
                    "describe the limitation of evaluating it from resume evidence."
                )
            if _UNSUPPORTED_CAPABILITY_ABSENCE.search(match.reason):
                errors.append(
                    f"not_assessable reason for '{match.requirement_name}' must "
                    "not claim that the candidate lacks the capability."
                )

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

        if match.status == MatchStatus.NOT_ASSESSABLE:
            continue

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
    not_assessable = []

    for match in match_result.matches:
        if match.status == MatchStatus.MATCHED:
            strengths.append(
                Strength(
                    area=match.requirement_name,
                    evidence=match.evidence,
                    reason=match.reason
                )
            )
        elif match.status in {MatchStatus.PARTIAL, MatchStatus.MISSING}:
            gaps.append(
                Gap(
                    area=match.requirement_name,
                    status=match.status,
                    evidence=match.evidence,
                    reason=match.reason
                )
            )
        elif match.status == MatchStatus.NOT_ASSESSABLE:
            not_assessable.append(
                NotAssessableRequirement(
                    area=match.requirement_name,
                    reason=match.reason,
                )
            )
        else:
            raise ValueError(f"Unsupported match status: {match.status}")

    return MatchAnalysis(
        strengths=strengths,
        gaps=gaps,
        not_assessable=not_assessable,
    )

