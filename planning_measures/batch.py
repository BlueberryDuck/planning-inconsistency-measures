"""
Batch measure computation for benchmark evaluation.

Processes all PDDL domain/problem pairs in a benchmark directory,
computes measures using plasp, and outputs results as CSV.

Usage:
    from planning_measures.batch import run_benchmark

    run_benchmark(
        "/path/to/benchmarks",
        "results.csv",
        skip_domains=KNOWN_INCOMPATIBLE,
    )
"""

import csv
import logging
import re
import time
from pathlib import Path

from .measures import compute_measures

logger = logging.getLogger(__name__)

# IPC 2016 domains known to be incompatible with plasp
KNOWN_INCOMPATIBLE = {
    "bag-barman",  # :equality not supported by plasp
    "tetris",  # :equality not supported by plasp
    "bag-gripper",  # grounding timeout (>120s)
    "bag-transport",  # grounding timeout (>120s)
    "over-nomystery",  # grounding timeout (>120s)
    "over-rovers",  # grounding timeout (>120s)
    "over-tpp",  # grounding timeout (>120s)
    "sliding-tiles",  # grounding timeout (>120s)
    "pegsol",  # grounding timeout (>120s)
}


def find_pddl_pairs(
    benchmark_dir: Path,
    skip_domains: set[str] | None = None,
) -> list[tuple[str, Path, Path]]:
    """
    Find all domain/problem pairs in a benchmark directory.

    Returns list of (domain_name, domain_path, problem_path) tuples.

    Args:
        benchmark_dir: Directory to scan
        skip_domains: Domain names to exclude (e.g. KNOWN_INCOMPATIBLE)

    Handles IPC naming conventions:
    - domain.pddl + prob*.pddl / satprob*.pddl
    - dom01.pddl + prob01.pddl (numbered pairs)
    """
    pairs = []
    skip = skip_domains or set()

    # Check if benchmark_dir contains domain subdirectories or is a single domain
    domain_dirs = []
    if (benchmark_dir / "domain.pddl").exists() or list(
        benchmark_dir.glob("dom[0-9]*.pddl")
    ):
        # Single domain directory
        domain_dirs.append(("", benchmark_dir))
    else:
        # Multiple domain subdirectories
        for subdir in sorted(benchmark_dir.iterdir()):
            if subdir.is_dir() and subdir.name not in skip:
                domain_dirs.append((subdir.name, subdir))

    for domain_name, domain_dir in domain_dirs:
        # Find domain file(s)
        single_domain = domain_dir / "domain.pddl"

        if single_domain.exists():
            # Single domain file: pair with all prob*.pddl and satprob*.pddl
            for prob in sorted(domain_dir.glob("*.pddl")):
                if prob.name == "domain.pddl":
                    continue
                label = domain_name or domain_dir.name
                pairs.append((label, single_domain, prob))
        else:
            # Numbered domain files: match dom01 with prob01
            for dom_file in sorted(domain_dir.glob("dom[0-9]*.pddl")):
                match = re.match(r"dom(\d+)\.pddl", dom_file.name)
                if not match:
                    continue
                num = match.group(1)
                prob = domain_dir / f"prob{num}.pddl"
                if prob.exists():
                    label = domain_name or domain_dir.name
                    pairs.append((label, dom_file, prob))
                # Also check for satprob
                satprob = domain_dir / f"satprob{num}.pddl"
                if satprob.exists():
                    pairs.append((label, dom_file, satprob))

    return pairs


def _compute_single(
    domain_name: str, domain_path: Path, problem_path: Path, horizon: int
) -> dict:
    """Compute measures for a single problem. Returns result dict."""
    start = time.time()
    try:
        profile = compute_measures(
            problem_path, domain_path=domain_path, horizon=horizon
        )
        elapsed = time.time() - start
        return {
            "domain": domain_name,
            "problem": problem_path.stem,
            "ur_scope": profile.ur_scope,
            "ur_struct": profile.ur_struct,
            "mx_scope": profile.mx_scope,
            "mx_struct": profile.mx_struct,
            "gs_scope": profile.gs_scope,
            "gs_struct": profile.gs_struct,
            "category": profile.category,
            "time_s": round(elapsed, 2),
            "status": "OK",
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "domain": domain_name,
            "problem": problem_path.stem,
            "ur_scope": "",
            "ur_struct": "",
            "mx_scope": "",
            "mx_struct": "",
            "gs_scope": "",
            "gs_struct": "",
            "category": "",
            "time_s": round(elapsed, 2),
            "status": f"ERROR: {str(e)[:100]}",
        }


CSV_FIELDS = [
    "domain",
    "problem",
    "ur_scope",
    "ur_struct",
    "mx_scope",
    "mx_struct",
    "gs_scope",
    "gs_struct",
    "category",
    "time_s",
    "status",
]


def run_benchmark(
    benchmark_dir: str | Path,
    output_csv: str | Path = "results.csv",
    horizon: int = 20,
    skip_domains: set[str] | None = None,
) -> Path:
    """
    Run measure computation on all PDDL problems in a benchmark directory.

    Args:
        benchmark_dir: Directory containing PDDL benchmark domains
        output_csv: Path for CSV output
        horizon: Maximum exploration steps
        skip_domains: Domain names to exclude (pass KNOWN_INCOMPATIBLE
                      to skip domains that timeout or fail with plasp)

    Returns:
        Path to output CSV file
    """
    benchmark_dir = Path(benchmark_dir)
    output_csv = Path(output_csv)

    pairs = find_pddl_pairs(benchmark_dir, skip_domains=skip_domains)
    if not pairs:
        raise ValueError(f"No PDDL pairs found in {benchmark_dir}")

    logger.info("Found %d problems in %s", len(pairs), benchmark_dir)

    results = []
    ok_count = 0

    for i, (domain_name, domain_path, problem_path) in enumerate(pairs, 1):
        logger.info("[%d/%d] %s/%s", i, len(pairs), domain_name, problem_path.stem)

        result = _compute_single(domain_name, domain_path, problem_path, horizon)
        results.append(result)

        if result["status"] == "OK":
            logger.info(
                "  (%s,%s,%s,%s,%s,%s) [%ss]",
                result["ur_scope"],
                result["ur_struct"],
                result["mx_scope"],
                result["mx_struct"],
                result["gs_scope"],
                result["gs_struct"],
                result["time_s"],
            )
            ok_count += 1
        else:
            logger.warning("  %s [%ss]", result["status"], result["time_s"])

    # Write CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    logger.info("Done: %d/%d OK. Results: %s", ok_count, len(pairs), output_csv)

    return output_csv
