#!/usr/bin/env python3
"""
Interactive CLI for Planning Inconsistency Measures.

Run with: python cli.py
"""

import csv
import time
from pathlib import Path

from planning_measures import compute_measures


# ANSI colors for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def colored(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    return f"{color}{text}{Colors.END}"


def print_header(text: str):
    """Print a section header."""
    print()
    print(colored(f"{'=' * 60}", Colors.BLUE))
    print(colored(f"  {text}", Colors.BOLD))
    print(colored(f"{'=' * 60}", Colors.BLUE))
    print()


def print_menu(options: list[tuple[str, str]]):
    """Print a numbered menu."""
    for i, (key, desc) in enumerate(options, 1):
        print(f"  {colored(str(i), Colors.GREEN)}) {desc}")
    print(f"  {colored('q', Colors.RED)}) Quit")
    print()


def get_choice(prompt: str, max_choice: int) -> str | int:
    """Get user's menu choice."""
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
    """Get a file/directory path from user."""
    path_str = input(colored(f"{prompt}: ", Colors.YELLOW)).strip()
    if not path_str:
        return None
    path = Path(path_str).expanduser()
    if must_exist and not path.exists():
        print(colored(f"Path not found: {path}", Colors.RED))
        return None
    return path


def get_int(prompt: str, default: int) -> int:
    """Get an integer from user with default."""
    value = input(colored(f"{prompt} [{default}]: ", Colors.YELLOW)).strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        print(colored(f"Invalid number, using default: {default}", Colors.YELLOW))
        return default


# ============================================================
# Menu Actions
# ============================================================


def action_compute_single():
    """Compute measures for a single problem."""
    print_header("Compute Measures for Single Problem")

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


def action_batch_directory():
    """Process all .lp files in a directory."""
    print_header("Batch Process Directory")

    input_dir = get_path("Input directory")
    if not input_dir or not input_dir.is_dir():
        print(colored("Invalid directory", Colors.RED))
        return

    output_path = get_path("Output CSV file", must_exist=False)
    if not output_path:
        output_path = Path("results.csv")

    horizon = get_int("Horizon", 20)

    # Find all .lp files
    problems = sorted(input_dir.rglob("*.lp"))
    if not problems:
        print(colored(f"No .lp files found in {input_dir}", Colors.RED))
        return

    print()
    print(f"Found {len(problems)} problems")
    print(f"Output: {output_path}")
    print()

    results = []

    for i, problem_path in enumerate(problems, 1):
        print(f"[{i}/{len(problems)}] {problem_path.name}...", end=" ", flush=True)

        try:
            start = time.time()
            profile = compute_measures(problem_path, horizon=horizon)
            elapsed = time.time() - start

            print(f"{profile} [{profile.category}] {elapsed:.2f}s")

            results.append(
                {
                    "problem": problem_path.stem,
                    "ur_scope": profile.ur_scope,
                    "ur_struct": profile.ur_struct,
                    "mx_scope": profile.mx_scope,
                    "mx_struct": profile.mx_struct,
                    "gs_scope": profile.gs_scope,
                    "gs_struct": profile.gs_struct,
                    "category": profile.category,
                    "time_s": f"{elapsed:.3f}",
                    "status": "OK",
                }
            )
        except Exception as e:
            print(colored(f"ERROR: {e}", Colors.RED))
            results.append(
                {
                    "problem": problem_path.stem,
                    "ur_scope": "",
                    "ur_struct": "",
                    "mx_scope": "",
                    "mx_struct": "",
                    "gs_scope": "",
                    "gs_struct": "",
                    "category": "",
                    "time_s": "",
                    "status": f"ERROR: {e}",
                }
            )

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        fieldnames = [
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
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    ok_count = sum(1 for r in results if r["status"] == "OK")
    print()
    print(f"Results: {ok_count}/{len(results)} OK")
    print(f"Written to: {output_path}")


def action_translate_pddl():
    """Translate PDDL to ASP format."""
    print_header("Translate PDDL to ASP")

    domain_path = get_path("Domain file (.pddl)")
    if not domain_path:
        return

    problem_path = get_path("Problem file (.pddl)")
    if not problem_path:
        return

    output_path = get_path("Output file (.lp)", must_exist=False)
    if not output_path:
        output_path = Path(f"{problem_path.stem}.lp")

    try:
        from planning_measures import translate_pddl

        translate_pddl(domain_path, problem_path, output_path)
        print()
        print(colored(f"Written to: {output_path}", Colors.GREEN))

        # Offer to compute measures
        print()
        if (
            input("Compute measures for translated file? [y/N]: ").strip().lower()
            == "y"
        ):
            profile = compute_measures(output_path)
            print()
            print(profile.summary())

    except Exception as e:
        print(colored(f"Error: {e}", Colors.RED))


# ============================================================
# Main Menu
# ============================================================


def main():
    """Main interactive loop."""
    print()
    print(colored("+" + "=" * 58 + "+", Colors.BLUE))
    print(
        colored(
            "|     Planning Inconsistency Measures - Interactive CLI    |", Colors.BLUE
        )
    )
    print(colored("+" + "=" * 58 + "+", Colors.BLUE))

    menu_options = [
        ("compute", "Compute measures for a single problem"),
        ("batch", "Batch process a directory"),
        ("translate", "Translate PDDL to ASP format"),
    ]

    actions = {
        1: action_compute_single,
        2: action_batch_directory,
        3: action_translate_pddl,
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
