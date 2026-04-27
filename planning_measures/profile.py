"""
MeasureProfile and TimingProfile dataclasses representing diagnostic results.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TimingProfile:
    """
    Per-phase timing breakdown for a single measure computation.

    Attributes:
        translate_s: PDDL-to-ASP translation via plasp (0.0 for .lp input)
        ground_s: Clingo grounding phase
        solve_s: Clingo solving phase (brave reasoning)
        extract_s: Python measure extraction (set operations)
        total_s: Wall-clock total (may slightly exceed sum due to overhead)
    """

    translate_s: float = 0.0
    ground_s: float = 0.0
    solve_s: float = 0.0
    extract_s: float = 0.0
    total_s: float = 0.0

    @classmethod
    def field_names(cls) -> list[str]:
        """Schema for timing fields in CSV/dict output (ordered)."""
        return [
            "time_translate_s",
            "time_ground_s",
            "time_solve_s",
            "time_extract_s",
            "time_total_s",
        ]

    def as_dict(self) -> dict[str, float]:
        """Return timing as a dict keyed by `field_names()` (rounded to 4dp)."""
        attrs = ["translate_s", "ground_s", "solve_s", "extract_s", "total_s"]
        return {
            name: round(getattr(self, attr), 4)
            for name, attr in zip(self.field_names(), attrs)
        }


@dataclass(frozen=True)
class MeasureProfile:
    """
    Diagnostic profile for a planning problem.

    Contains six measures organized as three pairs (scope, struct):
    - P1 Unreachability: Goals/propositions that cannot be reached
    - P2 Mutex: Achievable goals that can never coexist
    - P3 Sequencing: Goal pairs where achieving one blocks the other

    Attributes:
        ur_scope: Number of unreachable goals
        ur_struct: Total unreachable propositions
        mx_scope: Number of goals involved in mutex conflicts
        mx_struct: Number of mutex pairs (unordered)
        gs_scope: Number of goals involved in sequencing conflicts
        gs_struct: Number of sequencing conflict pairs (ordered)
    """

    ur_scope: int
    ur_struct: int
    mx_scope: int
    mx_struct: int
    gs_scope: int
    gs_struct: int
    num_goals: int = 0
    num_props: int = 0
    num_operators: int = 0

    @classmethod
    def field_names(cls) -> list[str]:
        """Schema for measure-profile fields in CSV/dict output (ordered)."""
        return [
            "num_goals",
            "num_props",
            "num_operators",
            "ur_scope",
            "ur_struct",
            "mx_scope",
            "mx_struct",
            "gs_scope",
            "gs_struct",
            "category",
        ]

    def as_dict(self) -> dict:
        """Return profile as a dict keyed by `field_names()` (category derived)."""
        return {name: getattr(self, name) for name in self.field_names()}

    def as_tuple(self) -> tuple[int, int, int, int, int, int]:
        """Return profile as a 6-tuple."""
        return (
            self.ur_scope,
            self.ur_struct,
            self.mx_scope,
            self.mx_struct,
            self.gs_scope,
            self.gs_struct,
        )

    def __str__(self) -> str:
        """Format as (ur_scope,ur_struct,mx_scope,mx_struct,gs_scope,gs_struct)."""
        return f"({self.ur_scope},{self.ur_struct},{self.mx_scope},{self.mx_struct},{self.gs_scope},{self.gs_struct})"

    @property
    def category(self) -> str:
        """
        Classify the problem category based on measure values.

        Returns one of:
        - "2a": Unreachability detected
        - "2c-sequencing": Sequencing conflicts (implies mutex)
        - "2c-mutex": Only mutex conflicts (reversible)
        - "consistent": No conflicts detected
        """
        if self.ur_scope > 0:
            return "2a"
        elif self.gs_scope > 0:
            return "2c-sequencing"
        elif self.mx_scope > 0:
            return "2c-mutex"
        else:
            return "consistent"

    @property
    def is_consistent(self) -> bool:
        """True if all measures are zero (no conflicts detected)."""
        return self.as_tuple() == (0, 0, 0, 0, 0, 0)

    def summary(self) -> str:
        """Human-readable summary of the profile."""
        lines = [
            f"Profile: {self}",
            f"Category: {self.category}",
            f"Problem size: {self.num_goals} goals, {self.num_props} propositions, {self.num_operators} operators",
            "",
            "P1 Unreachability:",
            f"  - Unreachable goals: {self.ur_scope}",
            f"  - Total unreachable propositions: {self.ur_struct}",
            "",
            "P2 Mutex:",
            f"  - Goals in mutex: {self.mx_scope}",
            f"  - Mutex pairs: {self.mx_struct}",
            "",
            "P3 Sequencing:",
            f"  - Goals in sequencing conflicts: {self.gs_scope}",
            f"  - Conflict pairs (ordered): {self.gs_struct}",
        ]
        return "\n".join(lines)
