"""Core measure computation orchestrator.

Wires Translate -> Brave reasoning -> Extraction. The actual measure logic
(P1 unreachability, P2 mutex, P3 sequencing) lives in `extraction.py`.
"""

import logging
import time
from pathlib import Path

from .brave import run_brave_reasoning
from .extraction import extract_measures, extract_problem_size
from .pddl_pipeline import TranslatedProblem, translate_pddl
from .profile import MeasureResult, TimingProfile

logger = logging.getLogger(__name__)


def compute_measures(
    problem_path: Path | str,
    horizon: int = 20,
    domain_path: Path | str | None = None,
) -> MeasureResult:
    """Compute all six inconsistency measures for a planning problem.

    Accepts either:
    - A pre-translated `.lp` file (legacy mode, for test scenarios)
    - PDDL domain + problem files (uses plasp for translation)

    Args:
        problem_path: Path to `.lp` file (if domain_path is None) or
                      PDDL problem file (if domain_path is provided)
        horizon: Maximum steps for state space exploration.
                 Increase if solvable problems show non-zero measures.
                 Default: 20
        domain_path: Path to PDDL domain file. When provided, plasp
                     is used to translate PDDL to ASP.

    Returns:
        MeasureResult bundling profile + size + per-phase timing.

    Raises:
        FileNotFoundError: If any input file doesn't exist
        RuntimeError: If ASP solving or plasp translation fails
    """
    t_total_start = time.monotonic()
    problem_path = Path(problem_path)
    if not problem_path.exists():
        raise FileNotFoundError(f"Problem file not found: {problem_path}")

    logger.info("Computing measures for %s (horizon=%d)", problem_path.name, horizon)

    if domain_path is not None:
        domain_path = Path(domain_path)
        if not domain_path.exists():
            raise FileNotFoundError(f"Domain file not found: {domain_path}")
        translated = translate_pddl(domain_path, problem_path)
    else:
        translated = TranslatedProblem(problem_path)

    with translated as tp:
        brave = run_brave_reasoning(tp, horizon)
        translate_s = tp.translate_s

    t0 = time.monotonic()
    profile = extract_measures(brave.outcome)
    size = extract_problem_size(brave.outcome)
    t_extract = time.monotonic() - t0

    timing = TimingProfile(
        translate_s=translate_s,
        ground_s=brave.ground_s,
        solve_s=brave.solve_s,
        extract_s=t_extract,
        total_s=time.monotonic() - t_total_start,
    )

    logger.debug("Result: %s (category=%s)", profile, profile.category)
    logger.debug(
        "Timing: translate=%.3fs ground=%.3fs solve=%.3fs extract=%.3fs total=%.3fs",
        timing.translate_s,
        timing.ground_s,
        timing.solve_s,
        timing.extract_s,
        timing.total_s,
    )
    return MeasureResult(profile=profile, size=size, timing=timing)
