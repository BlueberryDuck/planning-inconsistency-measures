"""
Planning Inconsistency Measures

A library for computing diagnostic measures on classical planning problems.

Usage with pre-translated ASP files:
    from planning_measures import compute_measures

    result = compute_measures("problem.lp")
    print(result.profile.ur_scope)  # Unreachable goals count
    print(result.size.num_goals)    # Problem size
    print(result.timing.ground_s)   # Grounding time in seconds

Usage with PDDL files (requires plasp):
    result = compute_measures("problem.pddl", domain_path="domain.pddl")

Timeout-protected execution uses a discriminated `ExecutionResult` and a
subprocess when timeout > 0:
    from planning_measures import compute_with_timeout

    execution = compute_with_timeout("problem.pddl", "domain.pddl", horizon=20, timeout=60)
    if execution.status == "ok":
        result = execution.unwrap()
        print(result.summary())
"""

from .brave import BraveOutcome, BraveReasoningResult, run_brave_reasoning
from .execution import ExecutionResult, compute_with_timeout
from .extraction import extract_measures, extract_problem_size
from .measures import compute_measures
from .pddl_pipeline import TranslatedProblem, translate_pddl
from .profile import MeasureProfile, MeasureResult, ProblemSize, TimingProfile

__all__ = [
    "BraveOutcome",
    "BraveReasoningResult",
    "ExecutionResult",
    "MeasureProfile",
    "MeasureResult",
    "ProblemSize",
    "TimingProfile",
    "TranslatedProblem",
    "compute_measures",
    "compute_with_timeout",
    "extract_measures",
    "extract_problem_size",
    "run_brave_reasoning",
    "translate_pddl",
]
__version__ = "1.0.0"
