"""
Core measure computation.

This module implements the three diagnostic measures:
- P1: Unreachability (computed from true reachability via brave reasoning)
- P2: Mutex (computed from brave reasoning witnesses)
- P3: Sequencing (computed from brave reasoning witnesses)

All measures are derived from a single brave reasoning pass, which
explores the actual state space with delete effects up to a bounded
horizon.
"""

import logging
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from .pddl_preprocessor import strip_costs
from .profile import MeasureProfile
from .solver import solve_brave

logger = logging.getLogger(__name__)


def compute_measures(
    problem_path: Path | str,
    horizon: int = 20,
    domain_path: Path | str | None = None,
    timeout: int = 0,
) -> MeasureProfile:
    """
    Compute all six inconsistency measures for a planning problem.

    This is the main entry point for the library. Accepts either:
    - A pre-translated .lp file (legacy mode, for test scenarios)
    - PDDL domain + problem files (uses plasp for translation)

    Args:
        problem_path: Path to .lp file (if domain_path is None) or
                      PDDL problem file (if domain_path is provided)
        horizon: Maximum steps for state space exploration.
                 Increase if solvable problems show non-zero measures.
                 Default: 20
        domain_path: Path to PDDL domain file. When provided, plasp
                     is used to translate PDDL to ASP.
        timeout: Time limit in seconds for Clingo solving (0 = no limit)

    Returns:
        MeasureProfile containing all six measure values

    Raises:
        FileNotFoundError: If any input file doesn't exist
        RuntimeError: If ASP solving or plasp translation fails
        TimeoutError: If solving exceeds the time limit
    """
    problem_path = Path(problem_path)
    if not problem_path.exists():
        raise FileNotFoundError(f"Problem file not found: {problem_path}")

    logger.info("Computing measures for %s (horizon=%d)", problem_path.name, horizon)

    if domain_path is not None:
        # PDDL mode: preprocess and translate via plasp
        domain_path = Path(domain_path)
        if not domain_path.exists():
            raise FileNotFoundError(f"Domain file not found: {domain_path}")

        problem_path, use_bridge, cleanup = _translate_pddl(domain_path, problem_path)
    else:
        # ASP mode: use pre-translated .lp file directly
        use_bridge = False
        cleanup = None

    try:
        data = _collect_brave(problem_path, horizon, use_bridge, timeout)
    finally:
        if cleanup is not None:
            cleanup()

    profile = _measures_from_data(data)
    logger.debug("Result: %s (category=%s)", profile, profile.category)
    return profile


def _translate_pddl(
    domain_path: Path, problem_path: Path
) -> tuple[Path, bool, Callable]:
    """Translate PDDL to ASP via plasp. Returns (lp_path, use_bridge, cleanup_fn)."""
    logger.info(
        "Translating PDDL via plasp: %s + %s", domain_path.name, problem_path.name
    )
    domain_text = strip_costs(domain_path.read_text())
    problem_text = strip_costs(problem_path.read_text())

    tmpdir = tempfile.mkdtemp()
    tmp = Path(tmpdir)
    (tmp / "domain.pddl").write_text(domain_text)
    (tmp / "problem.pddl").write_text(problem_text)

    result = subprocess.run(
        ["plasp", "translate", str(tmp / "domain.pddl"), str(tmp / "problem.pddl")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        shutil.rmtree(tmpdir)
        raise RuntimeError(
            f"plasp translation failed for {domain_path} + {problem_path}: "
            f"{result.stderr.strip()}"
        )

    plasp_lp = tmp / "instance.lp"
    plasp_lp.write_text(result.stdout)

    def cleanup():
        shutil.rmtree(tmpdir, ignore_errors=True)

    return plasp_lp, True, cleanup


def _measures_from_data(data: dict) -> MeasureProfile:
    """Compute MeasureProfile from collected brave reasoning data."""
    goals = data["goals"]
    props = data["props"]
    truly_reachable = data["true_reachable"]

    unreachable_goals = goals - truly_reachable
    unreachable_props = props - truly_reachable

    ur_scope = len(unreachable_goals)
    ur_struct = len(unreachable_props)

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
        num_goals=len(goals),
        num_props=len(props),
        num_operators=len(data["operators"]),
    )


def _collect_brave(
    problem_path: Path, horizon: int, use_bridge: bool, timeout: int = 0
) -> dict:
    """Collect all measure data from a single brave reasoning pass."""
    data = {
        "goals": set(),
        "props": set(),
        "operators": set(),
        "true_reachable": set(),
        "coexist": set(),
        "g2_after_g1": set(),
    }

    def on_atom(name: str, args: tuple):
        if name == "goal" and len(args) == 1:
            data["goals"].add(args[0])
        elif name == "prop" and len(args) == 1:
            data["props"].add(args[0])
        elif name == "operator" and len(args) == 1:
            data["operators"].add(args[0])
        elif name == "true_reachable" and len(args) == 1:
            data["true_reachable"].add(args[0])
        elif name == "coexist_witness" and len(args) == 2:
            g1, g2 = args
            data["coexist"].add((g1, g2))
            data["coexist"].add((g2, g1))
        elif name == "g2_after_g1_witness" and len(args) == 2:
            data["g2_after_g1"].add(args)

    if not solve_brave(
        problem_path, horizon, on_atom, use_bridge=use_bridge, timeout=timeout
    ):
        raise RuntimeError(f"ASP solving failed for {problem_path}")

    logger.debug(
        "Brave data: %d goals, %d props, %d operators, %d reachable, %d coexist, %d g2_after_g1",
        len(data["goals"]),
        len(data["props"]),
        len(data["operators"]),
        len(data["true_reachable"]),
        len(data["coexist"]),
        len(data["g2_after_g1"]),
    )
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
