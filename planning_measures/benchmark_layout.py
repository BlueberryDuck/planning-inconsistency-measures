"""Benchmark layout discovery.

Walks a Benchmark directory and returns (Domain, Problem) pairs under
the supported IPC layout conventions. Owns `KNOWN_INCOMPATIBLE`, the set
of IPC 2016 domain names that plasp can't translate or that grind out
on grounding (kept here because it's discovery-time domain knowledge,
not a CSV concern).
"""

import re
from pathlib import Path

KNOWN_INCOMPATIBLE: set[str] = {
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


def discover(
    benchmark_dir: Path,
    skip_domains: set[str] | None = None,
) -> list[tuple[str, Path, Path]]:
    """Return (domain_name, domain_path, problem_path) triples for a Benchmark dir.

    Treats `benchmark_dir` as a single Domain root when it contains
    `domain.pddl`, `dom[0-9]*.pddl`, or `domain_*.pddl`; otherwise as a
    parent of Domain subdirectories.
    """
    skip = skip_domains or set()

    if _looks_like_domain_root(benchmark_dir):
        return _discover_one_domain(benchmark_dir, benchmark_dir.name)

    pairs: list[tuple[str, Path, Path]] = []
    for subdir in sorted(benchmark_dir.iterdir()):
        if subdir.is_dir() and subdir.name not in skip:
            pairs.extend(_discover_one_domain(subdir, subdir.name))
    return pairs


def _looks_like_domain_root(d: Path) -> bool:
    return (
        (d / "domain.pddl").exists()
        or any(d.glob("dom[0-9]*.pddl"))
        or any(d.glob("domain_*.pddl"))
    )


def _discover_one_domain(domain_dir: Path, label: str) -> list[tuple[str, Path, Path]]:
    pairs: list[tuple[str, Path, Path]] = []

    domain = domain_dir / "domain.pddl"
    if domain.exists():
        for prob in sorted(domain_dir.glob("*.pddl")):
            if prob.name == "domain.pddl":
                continue
            pairs.append((label, domain, prob))

    for dom_file in sorted(domain_dir.glob("dom[0-9]*.pddl")):
        match = re.match(r"dom(\d+)\.pddl", dom_file.name)
        if not match:
            continue
        num = match.group(1)
        prob = domain_dir / f"prob{num}.pddl"
        if prob.exists():
            pairs.append((label, dom_file, prob))
        satprob = domain_dir / f"satprob{num}.pddl"
        if satprob.exists():
            pairs.append((label, dom_file, satprob))

    for dom_file in sorted(domain_dir.glob("domain_*.pddl")):
        suffix = dom_file.name[len("domain_") :]
        prob = domain_dir / suffix
        if prob.exists():
            pairs.append((label, dom_file, prob))

    return pairs
