#!/usr/bin/env python3
"""
Batch PDDL to ASP Translator

Traverses benchmark directories and translates all domain/problem pairs
to thesis ASP format in parallel.

Usage:
  python batch_translate.py <benchmark_dir> [-o output_dir] [-j workers]

Example:
  python batch_translate.py ~/benchmarks/ipc2016 -o benchmarks/translated/ipc2016 -j 4
"""

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# Import translator from same package
from pddl_to_asp import translate
from pddl import parse_domain, parse_problem


def find_pddl_pairs(benchmark_dir: Path) -> list[tuple[Path, Path, str]]:
    """
    Find all domain/problem pairs in a benchmark directory.

    Returns list of (domain_path, problem_path, relative_output_path) tuples.

    Handles common benchmark structures:
    - domain.pddl + pXX.pddl / instanceXX.pddl / problemXX.pddl
    - domainXX.pddl + problemXX.pddl (matched by number)
    - <subdir>/domain.pddl + <subdir>/pXX.pddl
    """
    pairs = []

    # Find all domain files
    domain_files = list(benchmark_dir.rglob("*domain*.pddl"))

    for domain_file in domain_files:
        domain_dir = domain_file.parent

        # Determine the domain name for output path
        rel_path = domain_dir.relative_to(benchmark_dir)

        # Find problem files in the same directory
        problem_patterns = [
            "p[0-9]*.pddl",
            "problem*.pddl",
            "instance*.pddl",
            "task*.pddl",
        ]

        problem_files = []
        for pattern in problem_patterns:
            problem_files.extend(domain_dir.glob(pattern))

        # Handle case where domain file contains a number (domainXX.pddl)
        if not problem_files and domain_file.stem.startswith("domain"):
            # Try to find paired problem file
            domain_num = "".join(c for c in domain_file.stem if c.isdigit())
            if domain_num:
                for pattern in [f"problem{domain_num}.pddl", f"p{domain_num}.pddl"]:
                    prob = domain_dir / pattern
                    if prob.exists():
                        problem_files.append(prob)

        # Add pairs
        for problem_file in problem_files:
            # Skip if the file is actually a domain file
            if "domain" in problem_file.stem.lower():
                continue

            output_name = f"{rel_path}_{problem_file.stem}.lp" if str(rel_path) != "." else f"{problem_file.stem}.lp"
            output_name = output_name.replace("/", "_").replace("\\", "_")
            pairs.append((domain_file, problem_file, output_name))

    return pairs


def translate_pair(args: tuple[Path, Path, Path]) -> tuple[str, bool, str]:
    """
    Translate a single domain/problem pair.

    Returns (output_name, success, message)
    """
    domain_file, problem_file, output_file = args

    try:
        domain = parse_domain(domain_file)
        problem = parse_problem(problem_file)
        output = translate(domain, problem)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(output)

        return (output_file.name, True, "OK")

    except Exception as e:
        return (output_file.name if output_file else str(problem_file), False, str(e))


def main():
    parser = argparse.ArgumentParser(
        description="Batch translate PDDL benchmarks to thesis ASP format"
    )
    parser.add_argument("benchmark_dir", type=Path, help="Directory containing PDDL benchmarks")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("benchmarks/translated"),
        help="Output directory (default: benchmarks/translated)"
    )
    parser.add_argument(
        "-j", "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be translated without doing it"
    )

    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"Error: Benchmark directory not found: {args.benchmark_dir}", file=sys.stderr)
        sys.exit(1)

    # Find all PDDL pairs
    pairs = find_pddl_pairs(args.benchmark_dir)

    if not pairs:
        print(f"No PDDL domain/problem pairs found in {args.benchmark_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(pairs)} PDDL problem(s) to translate")

    if args.dry_run:
        for domain, problem, output_name in pairs:
            print(f"  {problem.relative_to(args.benchmark_dir)} -> {output_name}")
        sys.exit(0)

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Prepare translation tasks
    tasks = [
        (domain, problem, args.output / output_name)
        for domain, problem, output_name in pairs
    ]

    # Run translations in parallel
    success_count = 0
    fail_count = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(translate_pair, task): task for task in tasks}

        for future in as_completed(futures):
            name, success, message = future.result()
            if success:
                success_count += 1
                if args.verbose:
                    print(f"  OK: {name}")
            else:
                fail_count += 1
                print(f"  FAIL: {name}: {message}", file=sys.stderr)

    print(f"\nResults: {success_count} translated, {fail_count} failed")
    print(f"Output: {args.output}")

    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
