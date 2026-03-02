"""
Clingo solver wrapper for ASP-based computation.
"""

import logging
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
    timeout: int = 0,
) -> bool:
    """
    Run brave reasoning (union of all answer sets).

    Args:
        problem_path: Path to the problem .lp file
        horizon: State exploration depth
        on_atom: Callback receiving (predicate_name, arguments) for each shown atom
        use_bridge: If True, load the plasp bridge encoding (for plasp-translated input)
        timeout: Time limit in seconds (0 = no limit)

    Returns:
        True if satisfiable, False otherwise

    Raises:
        TimeoutError: If the solve process exceeds the time limit
    """
    args = [
        f"-c horizon={horizon}",
        "--warn=no-atom-undefined",
        "--enum-mode=brave",
        "0",
    ]
    if timeout > 0:
        args.append(f"--time-limit={timeout}")

    ctl = clingo.Control(args)

    logger.debug("Loading encodings (horizon=%d, bridge=%s)", horizon, use_bridge)

    if use_bridge:
        ctl.load(str(BRIDGE_PLASP_LP))
    ctl.load(str(PLANNING_LP))
    ctl.load(str(REACHABILITY_LP))
    ctl.load(str(problem_path))

    ctl.ground([("base", [])])

    satisfiable = False
    atom_count = 0

    def on_model(model):
        nonlocal satisfiable, atom_count
        satisfiable = True
        for atom in model.symbols(shown=True):
            atom_count += 1
            args = tuple(
                arg.number if arg.type == clingo.SymbolType.Number else str(arg)
                for arg in atom.arguments
            )
            on_atom(atom.name, args)

    result = ctl.solve(on_model=on_model)

    if result.interrupted:
        raise TimeoutError(
            f"Solve exceeded {timeout}s time limit for {problem_path.name}"
        )

    logger.info(
        "Solve complete: %s (%d atoms)",
        "SAT" if satisfiable else "UNSAT",
        atom_count,
    )
    return satisfiable
