"""Pure set-algebra extraction over a `BraveOutcome`.

No Clingo dependency. Consumes the typed handoff produced by Brave reasoning
and computes the six-measure `MeasureProfile` and the `ProblemSize`.
"""

from .brave import BraveOutcome
from .profile import MeasureProfile, ProblemSize


def extract_measures(outcome: BraveOutcome) -> MeasureProfile:
    """Compute the 6-measure profile from a BraveOutcome (pure)."""
    unreachable_goals = outcome.goals - outcome.true_reachable
    unreachable_props = outcome.props - outcome.true_reachable
    achievable_goals = outcome.goals & outcome.true_reachable

    mx_scope, mx_struct = _mutex(achievable_goals, outcome.coexist_witness)
    gs_scope, gs_struct = _sequencing(achievable_goals, outcome.g2_after_g1_witness)

    return MeasureProfile(
        ur_scope=len(unreachable_goals),
        ur_struct=len(unreachable_props),
        mx_scope=mx_scope,
        mx_struct=mx_struct,
        gs_scope=gs_scope,
        gs_struct=gs_struct,
    )


def extract_problem_size(outcome: BraveOutcome) -> ProblemSize:
    """Cardinalities of goals, propositions, operators."""
    return ProblemSize(
        num_goals=len(outcome.goals),
        num_props=len(outcome.props),
        num_operators=len(outcome.operators),
    )


def _mutex(
    achievable_goals: frozenset[str],
    coexist_witnesses: frozenset[tuple[str, str]],
) -> tuple[int, int]:
    """P2: pair (g1, g2) is mutex iff *neither* (g1, g2) nor (g2, g1) is a witness."""
    mutex_pairs: set[tuple[str, str]] = set()
    goals_in_mutex: set[str] = set()

    sorted_goals = sorted(achievable_goals)
    for i, g1 in enumerate(sorted_goals):
        for g2 in sorted_goals[i + 1 :]:
            if (g1, g2) not in coexist_witnesses and (g2, g1) not in coexist_witnesses:
                mutex_pairs.add((g1, g2))
                goals_in_mutex.add(g1)
                goals_in_mutex.add(g2)

    return len(goals_in_mutex), len(mutex_pairs)


def _sequencing(
    achievable_goals: frozenset[str],
    g2_after_g1_witnesses: frozenset[tuple[str, str]],
) -> tuple[int, int]:
    """P3: ordered pair (g1, g2) is a sequencing conflict iff witness absent."""
    conflicts: set[tuple[str, str]] = set()
    goals_in_conflict: set[str] = set()

    for g1 in achievable_goals:
        for g2 in achievable_goals:
            if g1 != g2 and (g1, g2) not in g2_after_g1_witnesses:
                conflicts.add((g1, g2))
                goals_in_conflict.add(g1)
                goals_in_conflict.add(g2)

    return len(goals_in_conflict), len(conflicts)
