"""
CLI for Planning Inconsistency Measures.

Installed as `planning-measures` console script via pyproject.toml entry point.
"""

import argparse
import logging
import multiprocessing as mp
import sys
import time
from pathlib import Path

from planning_measures import compute_measures
from planning_measures.batch import run_benchmark


def _check_path(path: Path) -> None:
    """Check if a path exists, with a hint about benchmarks/ if applicable."""
    if path.exists():
        return
    parts = path.parts
    if len(parts) > 1 and parts[0] == "benchmarks" and not Path("benchmarks").exists():
        print(
            f"Error: {path} not found.\n\n"
            "No 'benchmarks' directory exists. Symlink or copy your benchmark data:\n"
            "  ln -s /path/to/benchmarks benchmarks",
            file=sys.stderr,
        )
    else:
        print(f"Error: {path} not found.", file=sys.stderr)
    sys.exit(1)


def _compute_worker(queue, problem, domain, horizon):
    """Child process for timeout-protected compute."""
    try:
        from planning_measures import compute_measures as _compute

        profile, timing = _compute(problem, domain_path=domain, horizon=horizon)
        queue.put(("ok", (profile, timing)))
    except Exception as e:
        queue.put(("error", f"{type(e).__name__}: {e}"))


def cmd_compute(args):
    """Compute measures for a single problem."""
    path = Path(args.problem)
    _check_path(path)
    domain_path = Path(args.domain) if args.domain else None
    if domain_path:
        _check_path(domain_path)

    print(f"Computing measures for {path.name}...", flush=True)

    start = time.monotonic()
    timeout = args.timeout

    if timeout > 0:
        ctx = mp.get_context("spawn")
        queue = ctx.Queue()
        proc = ctx.Process(
            target=_compute_worker,
            args=(
                queue,
                str(path),
                str(domain_path) if domain_path else None,
                args.horizon,
            ),
        )
        proc.start()
        proc.join(timeout=timeout)

        if proc.is_alive():
            proc.kill()
            proc.join()
            elapsed = time.monotonic() - start
            print(f"\nTimed out after {elapsed:.1f}s", file=sys.stderr)
            sys.exit(1)

        status, value = queue.get_nowait()
        if status == "error":
            print(f"\n{value}", file=sys.stderr)
            sys.exit(1)
        profile, timing = value
    else:
        profile, timing = compute_measures(
            path, domain_path=domain_path, horizon=args.horizon
        )

    print()
    print(profile.summary())
    print("\nTiming breakdown:")
    if timing.translate_s > 0:
        print(f"  Translation: {timing.translate_s:.3f}s")
    print(f"  Grounding:   {timing.ground_s:.3f}s")
    print(f"  Solving:     {timing.solve_s:.3f}s")
    print(f"  Extraction:  {timing.extract_s:.3f}s")
    print(f"  Total:       {timing.total_s:.3f}s")


def cmd_batch(args):
    """Batch process a benchmark directory."""
    logging.getLogger("planning_measures.batch").setLevel(logging.INFO)

    input_dir = Path(args.directory)
    _check_path(input_dir)
    output_path = Path(args.output)

    run_benchmark(input_dir, output_path, horizon=args.horizon, timeout=args.timeout)


def main():
    logging.basicConfig(level=logging.WARNING, format="%(name)s: %(message)s")

    parser = argparse.ArgumentParser(
        prog="planning-measures",
        description="Planning Inconsistency Measures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s compute tests/scenarios/p1_unreachability/locked_door.lp
  %(prog)s compute -d domain.pddl problem.pddl
  %(prog)s compute -d domain.pddl problem.pddl -H 30 -t 60
  %(prog)s batch benchmarks/diagnosis/
  %(prog)s batch benchmarks/diagnosis/ -o results/diagnosis.csv -t 120""",
    )
    sub = parser.add_subparsers(dest="command")

    # compute
    p_compute = sub.add_parser("compute", help="Compute measures for a single problem")
    p_compute.add_argument("problem", help="Problem file (.lp or .pddl)")
    p_compute.add_argument("-d", "--domain", help="Domain file (.pddl)")
    p_compute.add_argument(
        "-H", "--horizon", type=int, default=20, help="Search horizon (default: 20)"
    )
    p_compute.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=0,
        help="Timeout in seconds, 0=none (default: 0)",
    )

    # batch
    p_batch = sub.add_parser("batch", help="Batch process a benchmark directory")
    p_batch.add_argument("directory", help="Benchmark directory with PDDL files")
    p_batch.add_argument(
        "-o",
        "--output",
        default="results.csv",
        help="Output CSV path (default: results.csv)",
    )
    p_batch.add_argument(
        "-H", "--horizon", type=int, default=20, help="Search horizon (default: 20)"
    )
    p_batch.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=60,
        help="Timeout per problem in seconds (default: 60)",
    )

    args = parser.parse_args()

    if args.command == "compute":
        cmd_compute(args)
    elif args.command == "batch":
        cmd_batch(args)
    else:
        parser.print_help()
