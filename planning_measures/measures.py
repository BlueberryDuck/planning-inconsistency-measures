"""
Core measure computation.

This module implements the three diagnostic measures:
- P1: Unreachability (computed from true reachability via brave reasoning)
- P2: Mutex (computed from brave reasoning witnesses)
- P3: Sequencing (computed from brave reasoning witnesses)

All measures are derived from the brave reasoning pass, which explores
the actual state space with delete effects. The delete-relaxed fixpoint
in Part 1 of reachability.lp is retained as a fast screening predicate
but is not used for measure values.
"""

from pathlib import Path

from .profile import MeasureProfile
from .solver import solve_brave


def compute_measures(problem_path: Path | str, horizon: int = 20) -> MeasureProfile:
    """
    Compute all six inconsistency measures for a planning problem.

    This is the main entry point for the library.

    Args:
        problem_path: Path to .lp file containing the planning problem
                      (init/1, goal/1, precond/2, add/2, delete/2 facts)
        horizon: Maximum steps for state space exploration.
                 Increase if solvable problems show non-zero measures.
                 Default: 20

    Returns:
        MeasureProfile containing all six measure values

    Raises:
        FileNotFoundError: If problem_path doesn't exist
        RuntimeError: If ASP solving fails

    Example:
        >>> profile = compute_measures("problem.lp")
        >>> print(profile)
        (1,3,0,0,0,0)
        >>> print(profile.category)
        "2a"
    """
    problem_path = Path(problem_path)
    if not problem_path.exists():
        raise FileNotFoundError(f"Problem file not found: {problem_path}")

    # Single brave reasoning pass provides all data
    data = _collect_brave(problem_path, horizon)

    # P1: Unreachability from true reachability
    goals = data["goals"]
    props = data["props"]
    truly_reachable = data["true_reachable"]

    unreachable_goals = goals - truly_reachable
    unreachable_props = props - truly_reachable

    ur_scope = len(unreachable_goals)
    ur_struct = len(unreachable_props)

    # P2/P3: Mutex and sequencing from witnesses
    achievable_goals = goals & truly_reachable

    mx_scope, mx_struct = _compute_mutex(achievable_goals, data["coexist"])
    gs_scope, gs_struct = _compute_sequencing(achievable_goals, data["g2_after_g1"])

    return MeasureProfile(
        ur_scope=ur_scope,
        ur_struct=ur_struct,
        mx_scope=mx_scope,
        mx_struct=mx_struct,
        gs_scope=gs_scope,
        gs_struct=gs_struct,
    )


def _collect_brave(problem_path: Path, horizon: int) -> dict:
    """Collect all measure data from a single brave reasoning pass."""
    data = {
        "goals": set(),
        "props": set(),
        "true_reachable": set(),
        "coexist": set(),
        "g2_after_g1": set(),
    }

    def on_atom(name: str, args: tuple):
        if name == "goal" and len(args) == 1:
            data["goals"].add(args[0])
        elif name == "prop" and len(args) == 1:
            data["props"].add(args[0])
        elif name == "true_reachable" and len(args) == 1:
            data["true_reachable"].add(args[0])
        elif name == "coexist_witness" and len(args) == 2:
            g1, g2 = args
            data["coexist"].add((g1, g2))
            data["coexist"].add((g2, g1))
        elif name == "g2_after_g1_witness" and len(args) == 2:
            data["g2_after_g1"].add(args)

    if not solve_brave(problem_path, horizon, on_atom):
        raise RuntimeError(f"ASP solving failed for {problem_path}")

    return data


def _compute_mutex(
    achievable_goals: set[str], coexist_witnesses: set[tuple[str, str]]
) -> tuple[int, int]:
    """
    Compute P2 mutex measures.

    A goal pair (g1, g2) is mutex if both are achievable but they
    never coexist in any reachable state.
    """
    mutex_pairs = set()
    goals_in_mutex = set()

    goals = sorted(achievable_goals)
    for i, g1 in enumerate(goals):
        for g2 in goals[i + 1 :]:
            if (g1, g2) not in coexist_witnesses:
                mutex_pairs.add((g1, g2))
                goals_in_mutex.add(g1)
                goals_in_mutex.add(g2)

    return len(goals_in_mutex), len(mutex_pairs)


def _compute_sequencing(
    achievable_goals: set[str], g2_after_g1_witnesses: set[tuple[str, str]]
) -> tuple[int, int]:
    """
    Compute P3 sequencing conflict measures.

    An ordered pair (g1, g2) is a sequencing conflict if both goals
    are achievable, but g2 can never be reached after achieving g1.
    """
    conflicts = set()
    goals_in_conflict = set()

    for g1 in achievable_goals:
        for g2 in achievable_goals:
            if g1 != g2 and (g1, g2) not in g2_after_g1_witnesses:
                conflicts.add((g1, g2))
                goals_in_conflict.add(g1)
                goals_in_conflict.add(g2)

    return len(goals_in_conflict), len(conflicts)
