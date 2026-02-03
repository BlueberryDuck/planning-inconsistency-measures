"""
Core measure computation.

This module implements the three diagnostic measures:
- P1: Unreachability (computed deterministically in ASP)
- P2: Mutex (computed from brave reasoning witnesses)
- P3: Sequencing (computed from brave reasoning witnesses)
"""

from pathlib import Path

from .profile import MeasureProfile
from .solver import solve_deterministic, solve_brave


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

    # Phase 1: Deterministic solving for P1 and base facts
    p1_data = _collect_deterministic(problem_path, horizon)

    # Phase 2: Brave reasoning for P2/P3 witnesses
    witnesses = _collect_witnesses(problem_path, horizon)

    # Phase 3: Compute P2/P3 from witnesses
    achievable_goals = p1_data["goals"] & p1_data["reachable"]

    mx_scope, mx_struct = _compute_mutex(achievable_goals, witnesses["coexist"])
    gs_scope, gs_struct = _compute_sequencing(achievable_goals, witnesses["g2_after_g1"])

    return MeasureProfile(
        ur_scope=p1_data["ur_scope"],
        ur_struct=p1_data["ur_struct"],
        mx_scope=mx_scope,
        mx_struct=mx_struct,
        gs_scope=gs_scope,
        gs_struct=gs_struct,
    )


def _collect_deterministic(problem_path: Path, horizon: int) -> dict:
    """Collect P1 measures and base facts from deterministic solving."""
    data = {
        "goals": set(),
        "reachable": set(),
        "ur_scope": 0,
        "ur_struct": 0,
    }

    def on_atom(name: str, args: tuple):
        if name == "goal" and len(args) == 1:
            data["goals"].add(args[0])
        elif name == "reachable_prop" and len(args) == 1:
            data["reachable"].add(args[0])
        elif name == "i_ur_scope" and len(args) == 1:
            data["ur_scope"] = args[0]
        elif name == "i_ur_struct" and len(args) == 1:
            data["ur_struct"] = args[0]

    if not solve_deterministic(problem_path, horizon, on_atom):
        raise RuntimeError(f"ASP solving failed for {problem_path}")

    return data


def _collect_witnesses(problem_path: Path, horizon: int) -> dict:
    """Collect P2/P3 witnesses from brave reasoning."""
    witnesses = {
        "coexist": set(),      # (g1, g2) pairs that coexist somewhere
        "g2_after_g1": set(),  # (g1, g2) pairs where g2 reachable after g1
    }

    def on_atom(name: str, args: tuple):
        if name == "coexist_witness" and len(args) == 2:
            g1, g2 = args
            # Store both orderings for easier lookup
            witnesses["coexist"].add((g1, g2))
            witnesses["coexist"].add((g2, g1))
        elif name == "g2_after_g1_witness" and len(args) == 2:
            witnesses["g2_after_g1"].add(args)

    solve_brave(problem_path, horizon, on_atom)
    return witnesses


def _compute_mutex(
    achievable_goals: set[str],
    coexist_witnesses: set[tuple[str, str]]
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
        for g2 in goals[i + 1:]:  # Unordered pairs: g1 < g2
            if (g1, g2) not in coexist_witnesses:
                mutex_pairs.add((g1, g2))
                goals_in_mutex.add(g1)
                goals_in_mutex.add(g2)

    return len(goals_in_mutex), len(mutex_pairs)


def _compute_sequencing(
    achievable_goals: set[str],
    g2_after_g1_witnesses: set[tuple[str, str]]
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
