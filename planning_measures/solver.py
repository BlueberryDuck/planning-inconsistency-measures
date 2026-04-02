"""
Clingo solver wrapper for ASP-based computation.
"""

import logging
import time
from collections.abc import Callable
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
    on_atom: Callable[[str, tuple], None],
    use_bridge: bool = False,
) -> tuple[bool, float, float]:
    """
    Run brave reasoning (union of all answer sets).

    Args:
        problem_path: Path to the problem .lp file
        horizon: State exploration depth
        on_atom: Callback receiving (predicate_name, arguments) for each shown atom
        use_bridge: If True, load the plasp bridge encoding (for plasp-translated input)

    Returns:
        Tuple of (satisfiable, ground_time, solve_time) where times are in seconds.
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

    satisfiable = False
    atom_count = 0

    def on_model(model):
        nonlocal satisfiable, atom_count
        satisfiable = True
        for atom in model.symbols(shown=True):
            atom_count += 1
            solve_args = tuple(
                arg.number if arg.type == clingo.SymbolType.Number else str(arg)
                for arg in atom.arguments
            )
            on_atom(atom.name, solve_args)

    t1 = time.monotonic()
    ctl.solve(on_model=on_model)
    t_solve = time.monotonic() - t1

    logger.info(
        "Solve complete: %s (%d atoms, ground=%.3fs, solve=%.3fs)",
        "SAT" if satisfiable else "UNSAT",
        atom_count,
        t_ground,
        t_solve,
    )
    return satisfiable, t_ground, t_solve
