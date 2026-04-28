"""Extraction layer: brave-reasoning atoms -> MeasureProfile / ProblemSize.

Pure functions over a typed `BraveOutcome`. No Clingo dependency.

The atom-name vocabulary (`KEEP_ATOMS`) lives here so the solver wrapper can
stay generic — it just filters by these names.
"""

from dataclasses import dataclass

from .profile import MeasureProfile, ProblemSize

KEEP_ATOMS: frozenset[str] = frozenset(
    {
        "goal",
        "prop",
        "operator",
        "true_reachable",
        "coexist_witness",
        "g2_after_g1_witness",
    }
)


@dataclass(frozen=True)
class BraveOutcome:
    """Raw atom sets produced by a single brave-reasoning pass.

    No pre-derived intersections. `extract_measures` does the set algebra so
    test inputs stay faithful to the solver output.
    """

    goals: frozenset[str]
    props: frozenset[str]
    operators: frozenset[str]
    true_reachable: frozenset[str]
    coexist_witness: frozenset[tuple[str, str]]
    g2_after_g1_witness: frozenset[tuple[str, str]]


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


def collect(buckets: dict[str, list[tuple]]) -> BraveOutcome:
    """Wrap solver bucket dict into a typed BraveOutcome.

    The solver returns `dict[atom_name -> list[args_tuple]]` filtered by
    KEEP_ATOMS. This function shapes those buckets into the typed outcome.
    Missing keys default to empty.
    """

    def unary(name: str) -> frozenset[str]:
        return frozenset(args[0] for args in buckets.get(name, ()))

    def binary(name: str) -> frozenset[tuple[str, str]]:
        return frozenset((args[0], args[1]) for args in buckets.get(name, ()))

    return BraveOutcome(
        goals=unary("goal"),
        props=unary("prop"),
        operators=unary("operator"),
        true_reachable=unary("true_reachable"),
        coexist_witness=binary("coexist_witness"),
        g2_after_g1_witness=binary("g2_after_g1_witness"),
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
