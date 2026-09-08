from backend.models.analysis import CareerActionPlan, Gap
from backend.services.ai_service import generate_career_action_plan

def validate_career_action_plan(
    plan: CareerActionPlan,
    gaps: list[Gap],
) -> None:
    action_titles = [action.title for action in plan.actions]
    valid_gaps = {gap.area for gap in gaps}

    # 1. Action titles must be unique
    if len(action_titles) != len(set(action_titles)):
        raise ValueError("Action titles must be unique.")

    # 2. Priorities must be unique and sequential
    priorities = [action.priority for action in plan.actions]
    expected_priorities = list(range(1, len(plan.actions) + 1))

    if sorted(priorities) != expected_priorities:
        raise ValueError(
            f"Priorities must be sequential from 1 to {len(plan.actions)}."
        )

    # 3. All addressed gaps must exist in the original input
    for action in plan.actions:
        for gap_name in action.addresses_gaps:
            if gap_name not in valid_gaps:
                raise ValueError(
                    f"Unknown gap '{gap_name}' in action '{action.title}'."
                )

    # 4. Dependencies must reference real actions
    for action in plan.actions:
        for dependency in action.depends_on:
            if dependency not in action_titles:
                raise ValueError(
                    f"Unknown dependency '{dependency}' "
                    f"in action '{action.title}'."
                )

    # 5. Every input gap must be addressed
    addressed_gaps = {
        gap_name
        for action in plan.actions
        for gap_name in action.addresses_gaps
    }

    missing_gaps = valid_gaps - addressed_gaps

    if missing_gaps:
        raise ValueError(
            f"Plan does not address gaps: {sorted(missing_gaps)}"
        )


    dependency_graph = {
        action.title: action.depends_on
        for action in plan.actions
    }

    visiting = set()
    visited = set()

    def has_cycle(action_title: str) -> bool:
        if action_title in visiting:
            return True

        if action_title in visited:
            return False

        visiting.add(action_title)

        for dependency in dependency_graph[action_title]:
            if has_cycle(dependency):
                return True

        visiting.remove(action_title)
        visited.add(action_title)

        return False

    for action_title in action_titles:
        if has_cycle(action_title):
            raise ValueError("Plan contains a circular dependency.")

def create_validated_career_action_plan(
    gaps: list[Gap],
    max_attempts: int = 3,
) -> CareerActionPlan:

    if not gaps:
        return CareerActionPlan(actions=[])

    last_error = None
    validation_feedback = None

    for _ in range(max_attempts):
        plan = generate_career_action_plan(
            gaps,
            validation_feedback=validation_feedback,
        )

        try:
            validate_career_action_plan(plan, gaps)
            return plan

        except ValueError as error:
            last_error = error
            validation_feedback = str(error)

    raise ValueError(
        f"Failed to generate a valid career action plan "
        f"after {max_attempts} attempts. Last error: {last_error}"
    )