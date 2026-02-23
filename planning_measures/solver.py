"""
Clingo solver wrapper for ASP-based computation.
"""

from pathlib import Path
from typing import Callable

import clingo

_PACKAGE_DIR = Path(__file__).parent
ENCODINGS_DIR = _PACKAGE_DIR.parent / "encodings"

PLANNING_LP = ENCODINGS_DIR / "planning.lp"
REACHABILITY_LP = ENCODINGS_DIR / "reachability.lp"


def solve_brave(
    problem_path: Path, horizon: int, on_atom: Callable[[str, tuple], None]
) -> bool:
    """
    Run brave reasoning (union of all answer sets).

    Args:
        problem_path: Path to the problem .lp file
        horizon: State exploration depth
        on_atom: Callback receiving (predicate_name, arguments) for each shown atom

    Returns:
        True if satisfiable, False otherwise
    """
    ctl = clingo.Control(
        [
            f"-c horizon={horizon}",
            "--warn=no-atom-undefined",
            "--enum-mode=brave",
            "0",
        ]
    )

    ctl.load(str(PLANNING_LP))
    ctl.load(str(REACHABILITY_LP))
    ctl.load(str(problem_path))

    ctl.ground([("base", [])])

    satisfiable = False

    def on_model(model):
        nonlocal satisfiable
        satisfiable = True
        for atom in model.symbols(shown=True):
            args = tuple(
                arg.number if arg.type == clingo.SymbolType.Number else str(arg)
                for arg in atom.arguments
            )
            on_atom(atom.name, args)

    ctl.solve(on_model=on_model)
    return satisfiable
