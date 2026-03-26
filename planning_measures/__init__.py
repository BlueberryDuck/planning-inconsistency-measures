"""
Planning Inconsistency Measures

A library for computing diagnostic measures on classical planning problems.

Usage with pre-translated ASP files:
    from planning_measures import compute_measures, MeasureProfile

    profile = compute_measures("problem.lp")
    print(profile.ur_scope)  # Unreachable goals count

Usage with PDDL files (requires plasp):
    profile = compute_measures("problem.pddl", domain_path="domain.pddl")
"""

from .profile import MeasureProfile
from .measures import compute_measures

__all__ = ["MeasureProfile", "compute_measures"]
__version__ = "1.0.0"
