"""
Tests for planning inconsistency measures.

Run with: pytest tests/ -v
"""

import pytest
from pathlib import Path

from planning_measures import compute_measures, MeasureProfile


SCENARIOS_DIR = Path(__file__).parent / "scenarios"


# Expected profiles (from expected_profiles.txt)
EXPECTED = {
    "p1_unreachability/locked_door": (1, 3, 0, 0, 0, 0),
    "p1_unreachability/bank_vault": (1, 7, 0, 0, 0, 0),
    "p2_mutex/light_switch": (0, 0, 2, 1, 0, 0),
    "p2_mutex/traffic_light": (0, 0, 3, 3, 0, 0),
    "mixed/trust_travel": (0, 0, 2, 1, 2, 1),
    "mixed/rival_alliances": (0, 0, 2, 1, 2, 2),
    "edge_cases/coexisting_goals": (0, 0, 0, 0, 0, 0),
    "edge_cases/single_goal": (0, 0, 0, 0, 0, 0),
    "edge_cases/empty_goals": (0, 0, 0, 0, 0, 0),
    "edge_cases/delete_relaxation": (1, 1, 0, 0, 0, 0),
}


@pytest.mark.parametrize("scenario,expected", EXPECTED.items())
def test_scenario_profile(scenario: str, expected: tuple):
    """Each scenario should produce the expected measure profile."""
    path = SCENARIOS_DIR / f"{scenario}.lp"
    profile = compute_measures(path)
    assert profile.as_tuple() == expected


class TestMeasureProfile:
    """Tests for MeasureProfile dataclass."""

    def test_category_unreachability(self):
        p = MeasureProfile(1, 3, 0, 0, 0, 0)
        assert p.category == "2a"

    def test_category_sequencing(self):
        p = MeasureProfile(0, 0, 2, 1, 2, 1)
        assert p.category == "2c-sequencing"

    def test_category_mutex(self):
        p = MeasureProfile(0, 0, 2, 1, 0, 0)
        assert p.category == "2c-mutex"

    def test_category_consistent(self):
        p = MeasureProfile(0, 0, 0, 0, 0, 0)
        assert p.category == "consistent"
        assert p.is_consistent

    def test_str_format(self):
        p = MeasureProfile(1, 2, 3, 4, 5, 6)
        assert str(p) == "(1,2,3,4,5,6)"


class TestComputeMeasuresAPI:
    """Tests for the public compute_measures function."""

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Problem file not found"):
            compute_measures("nonexistent.lp")

    def test_accepts_path_object(self):
        profile = compute_measures(SCENARIOS_DIR / "edge_cases/single_goal.lp")
        assert profile.is_consistent

    def test_accepts_string_path(self):
        profile = compute_measures(str(SCENARIOS_DIR / "edge_cases/single_goal.lp"))
        assert profile.is_consistent

    def test_custom_horizon(self):
        # Should work with different horizon values
        profile = compute_measures(
            SCENARIOS_DIR / "edge_cases/single_goal.lp", horizon=10
        )
        assert profile.is_consistent


class TestMeasureHierarchy:
    """Tests for the diagnostic hierarchy (Proposition 11)."""

    def test_unreachable_excludes_other_conflicts(self):
        """Unreachable goals don't participate in mutex/sequencing."""
        profile = compute_measures(SCENARIOS_DIR / "p1_unreachability/locked_door.lp")
        assert profile.ur_scope > 0
        assert profile.mx_scope == 0
        assert profile.gs_scope == 0

    def test_sequencing_implies_mutex(self):
        """Sequencing conflicts imply mutex."""
        profile = compute_measures(SCENARIOS_DIR / "mixed/trust_travel.lp")
        assert profile.gs_scope > 0
        assert profile.mx_scope >= profile.gs_scope

    def test_mutex_without_sequencing_is_reversible(self):
        """Mutex without sequencing means reversible conflicts."""
        profile = compute_measures(SCENARIOS_DIR / "p2_mutex/light_switch.lp")
        assert profile.mx_scope > 0
        assert profile.gs_scope == 0

    def test_delete_effects_block_reachability(self):
        """Delete effects must prevent false reachability claims.

        Regression test: the delete-relaxed fixpoint marks c as reachable
        because a and b are individually reachable. But {a,b} never coexist
        due to o1 deleting a, so o2 is never applicable and c is unreachable.
        """
        profile = compute_measures(SCENARIOS_DIR / "edge_cases/delete_relaxation.lp")
        assert profile.ur_scope == 1  # c is unreachable
        assert profile.ur_struct == 1  # only c is unreachable (a, b both reachable)
        assert profile.mx_scope == 0  # no achievable goals to be mutex
        assert profile.gs_scope == 0
