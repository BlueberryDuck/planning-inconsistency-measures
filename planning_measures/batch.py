"""
Batch measure computation for benchmark evaluation.

Processes all PDDL domain/problem pairs in a benchmark directory,
computes measures using plasp, and outputs results as CSV with
per-phase timing breakdown (translate, ground, solve, extract).

Usage:
    from planning_measures.batch import run_benchmark
    from planning_measures.benchmark_layout import KNOWN_INCOMPATIBLE

    run_benchmark(
        "/path/to/benchmarks",
        "results.csv",
        skip_domains=KNOWN_INCOMPATIBLE,
    )
"""

import csv
import logging
from pathlib import Path

from .benchmark_layout import discover
from .execution import CSV_FIELDS, compute_with_timeout

logger = logging.getLogger(__name__)


def run_benchmark(
    benchmark_dir: str | Path,
    output_csv: str | Path = "results.csv",
    horizon: int = 20,
    skip_domains: set[str] | None = None,
    timeout: int = 0,
) -> Path:
    """
    Run measure computation on all PDDL problems in a benchmark directory.

    Args:
        benchmark_dir: Directory containing PDDL benchmark domains
        output_csv: Path for CSV output
        horizon: Maximum exploration steps
        skip_domains: Domain names to exclude (pass KNOWN_INCOMPATIBLE
                      to skip domains that timeout or fail with plasp)
        timeout: Time limit in seconds per problem (0 = no limit)

    Returns:
        Path to output CSV file
    """
    benchmark_dir = Path(benchmark_dir)
    output_csv = Path(output_csv)

    pairs = discover(benchmark_dir, skip_domains=skip_domains)
    if not pairs:
        raise ValueError(f"No PDDL pairs found in {benchmark_dir}")

    logger.info("Found %d problems in %s", len(pairs), benchmark_dir)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    ok_count = 0

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for i, (domain_name, domain_path, problem_path) in enumerate(pairs, 1):
            logger.info("[%d/%d] %s/%s", i, len(pairs), domain_name, problem_path.stem)

            execution = compute_with_timeout(
                problem_path, domain_path, horizon, timeout
            )
            row = execution.to_csv_row(domain_name, problem_path)
            writer.writerow(row)
            f.flush()

            if execution.status == "ok":
                result = execution.unwrap()
                logger.info(
                    "  %s [total=%.4fs ground=%.4fs solve=%.4fs]",
                    result.profile,
                    result.timing.total_s,
                    result.timing.ground_s,
                    result.timing.solve_s,
                )
                ok_count += 1
            else:
                logger.warning("  %s", execution.status_label())

    logger.info("Done: %d/%d OK. Results: %s", ok_count, len(pairs), output_csv)

    return output_csv
