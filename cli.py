#!/usr/bin/env python3
"""
Interactive CLI for Planning Inconsistency Measures.

Run with: python cli.py
"""

import logging
import time
from pathlib import Path

from planning_measures import compute_measures
from planning_measures.batch import run_benchmark


# ANSI colors for terminal output
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def colored(text: str, color: str) -> str:
    return f"{color}{text}{Colors.END}"


def print_header(text: str):
    print()
    print(colored(f"{'=' * 60}", Colors.BLUE))
    print(colored(f"  {text}", Colors.BOLD))
    print(colored(f"{'=' * 60}", Colors.BLUE))
    print()


def print_menu(options: list[tuple[str, str]]):
    for i, (_, desc) in enumerate(options, 1):
        print(f"  {colored(str(i), Colors.GREEN)}) {desc}")
    print(f"  {colored('q', Colors.RED)}) Quit")
    print()


def get_choice(prompt: str, max_choice: int) -> str | int:
    while True:
        choice = input(colored(f"{prompt}: ", Colors.YELLOW)).strip().lower()
        if choice == "q":
            return "q"
        try:
            num = int(choice)
            if 1 <= num <= max_choice:
                return num
        except ValueError:
            pass
        print(colored("Invalid choice. Try again.", Colors.RED))


def get_path(prompt: str, must_exist: bool = True) -> Path | None:
    path_str = input(colored(f"{prompt}: ", Colors.YELLOW)).strip()
    if not path_str:
        return None
    path = Path(path_str).expanduser()
    if must_exist and not path.exists():
        print(colored(f"Path not found: {path}", Colors.RED))
        return None
    return path


def get_int(prompt: str, default: int) -> int:
    value = input(colored(f"{prompt} [{default}]: ", Colors.YELLOW)).strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        print(colored(f"Invalid number, using default: {default}", Colors.YELLOW))
        return default


def action_compute_lp():
    """Compute measures for a pre-translated .lp file."""
    print_header("Compute Measures (ASP file)")

    path = get_path("Path to .lp file")
    if not path:
        return

    horizon = get_int("Horizon", 20)

    print()
    print(f"Computing measures for {path.name}...")

    try:
        start = time.time()
        profile = compute_measures(path, horizon=horizon)
        elapsed = time.time() - start

        print()
        print(profile.summary())
        print()
        print(f"Computed in {elapsed:.3f}s")
    except Exception as e:
        print(colored(f"Error: {e}", Colors.RED))


def action_compute_pddl():
    """Compute measures from PDDL domain + problem files."""
    print_header("Compute Measures (PDDL files)")

    domain_path = get_path("Domain file (.pddl)")
    if not domain_path:
        return

    problem_path = get_path("Problem file (.pddl)")
    if not problem_path:
        return

    horizon = get_int("Horizon", 20)

    print()
    print(f"Computing measures for {problem_path.name}...")

    try:
        start = time.time()
        profile = compute_measures(
            problem_path, domain_path=domain_path, horizon=horizon
        )
        elapsed = time.time() - start

        print()
        print(profile.summary())
        print()
        print(f"Computed in {elapsed:.3f}s")
    except Exception as e:
        print(colored(f"Error: {e}", Colors.RED))


def action_batch_benchmark():
    """Batch process a PDDL benchmark directory."""
    print_header("Batch Benchmark (PDDL)")

    input_dir = get_path("Benchmark directory")
    if not input_dir or not input_dir.is_dir():
        print(colored("Invalid directory", Colors.RED))
        return

    output_path = get_path("Output CSV file", must_exist=False)
    if not output_path:
        output_path = Path("results.csv")

    horizon = get_int("Horizon", 20)

    try:
        run_benchmark(input_dir, output_path, horizon=horizon)
    except Exception as e:
        print(colored(f"Error: {e}", Colors.RED))


def main():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(name)s: %(message)s",
    )

    print()
    print(colored("+" + "=" * 58 + "+", Colors.BLUE))
    print(
        colored(
            "|     Planning Inconsistency Measures - Interactive CLI    |",
            Colors.BLUE,
        )
    )
    print(colored("+" + "=" * 58 + "+", Colors.BLUE))

    menu_options = [
        ("lp", "Compute measures for a single .lp file"),
        ("pddl", "Compute measures from PDDL domain + problem"),
        ("batch", "Batch process a PDDL benchmark directory"),
    ]

    actions = {
        1: action_compute_lp,
        2: action_compute_pddl,
        3: action_batch_benchmark,
    }

    while True:
        print()
        print(colored("Main Menu", Colors.BOLD))
        print_menu(menu_options)

        choice = get_choice("Select option", len(menu_options))

        if choice == "q":
            print()
            print("Goodbye!")
            break

        actions[choice]()


if __name__ == "__main__":
    main()
