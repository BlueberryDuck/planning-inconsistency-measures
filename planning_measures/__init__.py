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
"""

from .profile import MeasureProfile, TimingProfile
from .measures import compute_measures

__all__ = ["MeasureProfile", "TimingProfile", "compute_measures"]
__version__ = "2.0.0"
