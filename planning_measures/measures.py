"""
Core measure computation orchestrator.

Wires translation -> solver -> extraction. The actual measure logic
(P1 unreachability, P2 mutex, P3 sequencing) lives in `extraction.py`.
"""

import logging
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from . import extraction
from .pddl_preprocessor import strip_costs
from .profile import MeasureResult, TimingProfile
from .solver import solve_brave

logger = logging.getLogger(__name__)


def compute_measures(
    problem_path: Path | str,
    horizon: int = 20,
    domain_path: Path | str | None = None,
) -> MeasureResult:
    """
    Compute all six inconsistency measures for a planning problem.

    Accepts either:
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

    t_translate = 0.0
    cleanup: Callable | None = None
    use_bridge = False
    if domain_path is not None:
        domain_path = Path(domain_path)
        if not domain_path.exists():
            raise FileNotFoundError(f"Domain file not found: {domain_path}")

        t0 = time.monotonic()
        problem_path, use_bridge, cleanup = _translate_pddl(domain_path, problem_path)
        t_translate = time.monotonic() - t0

    try:
        buckets, t_ground, t_solve = solve_brave(
            problem_path,
            horizon,
            keep_atoms=extraction.KEEP_ATOMS,
            use_bridge=use_bridge,
        )
    finally:
        if cleanup is not None:
            cleanup()

    t0 = time.monotonic()
    outcome = extraction.collect(buckets)
    profile = extraction.extract_measures(outcome)
    size = extraction.extract_problem_size(outcome)
    t_extract = time.monotonic() - t0

    timing = TimingProfile(
        translate_s=t_translate,
        ground_s=t_ground,
        solve_s=t_solve,
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
