"""Brave reasoning: ground + brave-solve a TranslatedProblem into a BraveReasoningResult.

Owns the atom vocabulary (`_KEEP_ATOMS`) and bucket decoding (`_collect`) as
private details. Callers receive a typed `BraveReasoningResult` carrying a
`BraveOutcome` and per-phase wall-clock timing.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import clingo

from .extraction import BraveOutcome
from .pddl_pipeline import TranslatedProblem

logger = logging.getLogger(__name__)

_PACKAGE_DIR = Path(__file__).parent
ENCODINGS_DIR = _PACKAGE_DIR.parent / "encodings"

PLANNING_LP = ENCODINGS_DIR / "planning.lp"
REACHABILITY_LP = ENCODINGS_DIR / "reachability.lp"
BRIDGE_PLASP_LP = ENCODINGS_DIR / "bridge_plasp.lp"

_KEEP_ATOMS: frozenset[str] = frozenset(
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
class BraveReasoningResult:
    """Envelope from Brave reasoning: a `BraveOutcome` plus per-phase timing."""

    outcome: BraveOutcome
    ground_s: float
    solve_s: float


def run_brave_reasoning(
    translated: TranslatedProblem, horizon: int
) -> BraveReasoningResult:
    """Ground + brave-solve a `TranslatedProblem`.

    Loads the plasp bridge encoding iff `translated.needs_bridge`. Raises
    `RuntimeError` on UNSAT.
    """
    args = [
        f"-c horizon={horizon}",
        "--warn=no-atom-undefined",
        "--enum-mode=brave",
        "0",
    ]

    ctl = clingo.Control(args)

    logger.debug(
        "Loading encodings (horizon=%d, bridge=%s)",
        horizon,
        translated.needs_bridge,
    )

    if translated.needs_bridge:
        ctl.load(str(BRIDGE_PLASP_LP))
    ctl.load(str(PLANNING_LP))
    ctl.load(str(REACHABILITY_LP))
    ctl.load(str(translated.path))

    t0 = time.monotonic()
    ctl.ground([("base", [])])
    ground_s = time.monotonic() - t0

    buckets: dict[str, list[tuple]] = {name: [] for name in _KEEP_ATOMS}
    satisfiable = False

    def on_model(model):
        nonlocal satisfiable
        satisfiable = True
        for atom in model.symbols(shown=True):
            name = atom.name
            if name not in _KEEP_ATOMS:
                continue
            args_tuple = tuple(
                arg.number if arg.type == clingo.SymbolType.Number else str(arg)
                for arg in atom.arguments
            )
            buckets[name].append(args_tuple)

    t1 = time.monotonic()
    ctl.solve(on_model=on_model)
    solve_s = time.monotonic() - t1

    logger.info(
        "Solve complete: %s (ground=%.3fs, solve=%.3fs)",
        "SAT" if satisfiable else "UNSAT",
        ground_s,
        solve_s,
    )

    if not satisfiable:
        raise RuntimeError(f"ASP solving failed for {translated.path}")

    return BraveReasoningResult(
        outcome=_collect(buckets),
        ground_s=ground_s,
        solve_s=solve_s,
    )


def _collect(buckets: dict[str, list[tuple]]) -> BraveOutcome:
    """Shape filter buckets into a typed BraveOutcome."""

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
