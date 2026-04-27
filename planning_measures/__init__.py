"""
Planning Inconsistency Measures

A library for computing diagnostic measures on classical planning problems.

Usage with pre-translated ASP files:
    from planning_measures import compute_measures, MeasureProfile

    profile, timing = compute_measures("problem.lp")
    print(profile.ur_scope)  # Unreachable goals count
    print(timing.ground_s)   # Grounding time in seconds

Usage with PDDL files (requires plasp):
    profile, timing = compute_measures("problem.pddl", domain_path="domain.pddl")

Timeout-protected execution uses a discriminated `ExecutionResult` and a
subprocess when timeout > 0:
    from planning_measures import compute_with_timeout

    result = compute_with_timeout("problem.pddl", "domain.pddl", horizon=20, timeout=60)
    if result.status == "ok":
        profile, timing = result.unwrap()
"""

from .execution import ExecutionResult, compute_with_timeout
from .measures import compute_measures
from .profile import MeasureProfile, TimingProfile

__all__ = [
    "ExecutionResult",
    "MeasureProfile",
    "TimingProfile",
    "compute_measures",
    "compute_with_timeout",
]
__version__ = "1.0.0"
