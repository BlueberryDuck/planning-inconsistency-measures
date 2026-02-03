"""
Batch PDDL to ASP Translator

Traverses benchmark directories and translates all domain/problem pairs
to thesis ASP format in parallel.

Usage:
    from planning_measures import batch_translate
    batch_translate("~/benchmarks", "output/", workers=4)
"""

import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from pddl import parse_domain, parse_problem

from .translator import translate


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

    # Find all domain files (including IPC dom[0-9]*.pddl pattern)
    domain_files = list(benchmark_dir.rglob("*domain*.pddl")) + list(
        benchmark_dir.rglob("dom[0-9]*.pddl")
    )
    domain_files = list(set(domain_files))  # Remove duplicates

    for domain_file in domain_files:
        domain_dir = domain_file.parent

        # Determine the domain name for output path
        rel_path = domain_dir.relative_to(benchmark_dir)

        # Find problem files in the same directory
        problem_patterns = [
            "p[0-9]*.pddl",
            "prob[0-9]*.pddl",
            "satprob[0-9]*.pddl",
            "problem*.pddl",
            "*_problem*.pddl",
            "instance*.pddl",
            "task*.pddl",
        ]

        problem_files = []
        for pattern in problem_patterns:
            problem_files.extend(domain_dir.glob(pattern))

        # Handle case where domain file contains a number (domainXX.pddl or domXX.pddl)
        if not problem_files:
            # Try to extract number from domain filename
            if match := re.match(r"^dom(?:ain)?(\d+)$", domain_file.stem):
                num = match.group(1)
                for prefix in ["prob", "p", "problem"]:
                    prob = domain_dir / f"{prefix}{num}.pddl"
                    if prob.exists():
                        problem_files.append(prob)
                        break

        # Add pairs
        for problem_file in problem_files:
            # Skip if the file is actually a domain file
            if "domain" in problem_file.stem.lower():
                continue

            output_name = (
                f"{rel_path}_{problem_file.stem}.lp"
                if str(rel_path) != "."
                else f"{problem_file.stem}.lp"
            )
            output_name = output_name.replace("/", "_").replace("\\", "_")
            pairs.append((domain_file, problem_file, output_name))

    return pairs


def _translate_pair(args: tuple[Path, Path, Path]) -> tuple[str, bool, str]:
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


def batch_translate(
    benchmark_dir: str | Path,
    output_dir: str | Path = "benchmarks/translated",
    workers: int = 4,
    verbose: bool = False,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Batch translate PDDL benchmarks to thesis ASP format.

    Args:
        benchmark_dir: Directory containing PDDL benchmarks
        output_dir: Output directory for translated files
        workers: Number of parallel workers
        verbose: Print progress
        dry_run: Show what would be translated without doing it

    Returns:
        Tuple of (success_count, fail_count)
    """
    benchmark_dir = Path(benchmark_dir)
    output_dir = Path(output_dir)

    if not benchmark_dir.exists():
        raise FileNotFoundError(f"Benchmark directory not found: {benchmark_dir}")

    # Find all PDDL pairs
    pairs = find_pddl_pairs(benchmark_dir)

    if not pairs:
        raise ValueError(f"No PDDL domain/problem pairs found in {benchmark_dir}")

    if verbose:
        print(f"Found {len(pairs)} PDDL problem(s) to translate")

    if dry_run:
        for domain, problem, output_name in pairs:
            print(f"  {problem.relative_to(benchmark_dir)} -> {output_name}")
        return (0, 0)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare translation tasks
    tasks = [
        (domain, problem, output_dir / output_name)
        for domain, problem, output_name in pairs
    ]

    # Run translations in parallel
    success_count = 0
    fail_count = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_translate_pair, task): task for task in tasks}

        for future in as_completed(futures):
            name, success, message = future.result()
            if success:
                success_count += 1
                if verbose:
                    print(f"  OK: {name}")
            else:
                fail_count += 1
                if verbose:
                    print(f"  FAIL: {name}: {message}", file=sys.stderr)

    if verbose:
        print(f"\nResults: {success_count} translated, {fail_count} failed")
        print(f"Output: {output_dir}")

    return (success_count, fail_count)
