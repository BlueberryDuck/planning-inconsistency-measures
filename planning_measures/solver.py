"""
Clingo solver wrapper for ASP-based computation.
"""

import logging
import time
from pathlib import Path

import clingo

logger = logging.getLogger(__name__)

_PACKAGE_DIR = Path(__file__).parent
ENCODINGS_DIR = _PACKAGE_DIR.parent / "encodings"

PLANNING_LP = ENCODINGS_DIR / "planning.lp"
REACHABILITY_LP = ENCODINGS_DIR / "reachability.lp"
BRIDGE_PLASP_LP = ENCODINGS_DIR / "bridge_plasp.lp"


def solve_brave(
    problem_path: Path,
    horizon: int,
    keep_atoms: frozenset[str],
    use_bridge: bool = False,
) -> tuple[dict[str, list[tuple]], float, float]:
    """
    Run brave reasoning (union of all answer sets) and bucket the kept atoms.

    Args:
        problem_path: Path to the problem .lp file
        horizon: State exploration depth
        keep_atoms: Atom names to retain. Atoms outside this set are dropped.
        use_bridge: If True, load the plasp bridge encoding (for plasp-translated input)

    Returns:
        Tuple of (buckets, ground_time, solve_time) where buckets is a dict
        keyed by atom name (only names in `keep_atoms` appear) mapping to a
        list of argument tuples. Times are in seconds.

    Raises:
        RuntimeError: If the program is UNSAT.
    """
    args = [
        f"-c horizon={horizon}",
        "--warn=no-atom-undefined",
        "--enum-mode=brave",
        "0",
    ]

    ctl = clingo.Control(args)

    logger.debug("Loading encodings (horizon=%d, bridge=%s)", horizon, use_bridge)

    if use_bridge:
        ctl.load(str(BRIDGE_PLASP_LP))
    ctl.load(str(PLANNING_LP))
    ctl.load(str(REACHABILITY_LP))
    ctl.load(str(problem_path))

    t0 = time.monotonic()
    ctl.ground([("base", [])])
    t_ground = time.monotonic() - t0

    buckets: dict[str, list[tuple]] = {name: [] for name in keep_atoms}
    satisfiable = False

    def on_model(model):
        nonlocal satisfiable
        satisfiable = True
        for atom in model.symbols(shown=True):
            name = atom.name
            if name not in keep_atoms:
                continue
            args_tuple = tuple(
                arg.number if arg.type == clingo.SymbolType.Number else str(arg)
                for arg in atom.arguments
            )
            buckets[name].append(args_tuple)

    t1 = time.monotonic()
    ctl.solve(on_model=on_model)
    t_solve = time.monotonic() - t1

    logger.info(
        "Solve complete: %s (ground=%.3fs, solve=%.3fs)",
        "SAT" if satisfiable else "UNSAT",
        t_ground,
        t_solve,
    )

    if not satisfiable:
        raise RuntimeError(f"ASP solving failed for {problem_path}")

    return buckets, t_ground, t_solve
