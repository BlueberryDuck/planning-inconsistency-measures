"""
Tests for planning inconsistency measures.

Run with: pytest tests/ -v
"""

from pathlib import Path

import pytest

from planning_measures import MeasureProfile, TimingProfile, compute_measures

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


# Expected profiles for each test scenario
EXPECTED = {
    "edge_cases/coexisting_goals": (0, 0, 0, 0, 0, 0),
    "edge_cases/delete_relaxation": (1, 1, 0, 0, 0, 0),
    "edge_cases/empty_goals": (0, 0, 0, 0, 0, 0),
    "edge_cases/negative_precondition": (1, 1, 0, 0, 0, 0),
    "edge_cases/single_goal": (0, 0, 0, 0, 0, 0),
    "mixed/rival_alliances": (0, 0, 2, 1, 2, 2),
    "mixed/trust_travel": (0, 0, 2, 1, 2, 1),
    "p1_unreachability/bank_vault": (1, 7, 0, 0, 0, 0),
    "p1_unreachability/locked_door": (1, 3, 0, 0, 0, 0),
    "p2_mutex/light_switch": (0, 0, 2, 1, 0, 0),
    "p2_mutex/traffic_light": (0, 0, 3, 3, 0, 0),
}


@pytest.mark.parametrize("scenario,expected", EXPECTED.items())
def test_scenario_profile(scenario: str, expected: tuple):
    """Each scenario should produce the expected measure profile."""
    path = SCENARIOS_DIR / f"{scenario}.lp"
    profile, _ = compute_measures(path)
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

    def test_field_names_order_matches_csv(self):
        """field_names locks the schema for CSV row composition."""
        assert MeasureProfile.field_names() == [
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

    def test_as_dict_keyed_by_field_names(self):
        """as_dict returns {field_names()[i]: value} with derived category."""
        p = MeasureProfile(1, 3, 0, 0, 0, 0, num_goals=2, num_props=5, num_operators=4)
        d = p.as_dict()
        assert list(d.keys()) == MeasureProfile.field_names()
        assert d["num_goals"] == 2
        assert d["ur_scope"] == 1
        assert d["category"] == "2a"


class TestComputeMeasuresAPI:
    """Tests for the public compute_measures function."""

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Problem file not found"):
            compute_measures("nonexistent.lp")

    def test_unsatisfiable_raises_error(self):
        """UNSAT problems should raise RuntimeError."""
        with pytest.raises(RuntimeError, match="ASP solving failed"):
            compute_measures(SCENARIOS_DIR / "edge_cases/unsatisfiable.lp")

    def test_horizon_sensitivity(self):
        """Insufficient horizon should report false unreachability."""
        # Chain a->b->c->d needs 3 steps; horizon=2 is too short
        short, _ = compute_measures(
            SCENARIOS_DIR / "edge_cases/horizon_sensitive.lp", horizon=2
        )
        assert short.ur_scope == 1  # d appears unreachable

        # Sufficient horizon resolves the chain
        full, _ = compute_measures(
            SCENARIOS_DIR / "edge_cases/horizon_sensitive.lp", horizon=3
        )
        assert full.is_consistent


class TestMeasureHierarchy:
    """Tests for the diagnostic hierarchy (Proposition 11)."""

    def test_unreachable_excludes_other_conflicts(self):
        """Unreachable goals don't participate in mutex/sequencing."""
        profile, _ = compute_measures(
            SCENARIOS_DIR / "p1_unreachability/locked_door.lp"
        )
        assert profile.ur_scope > 0
        assert profile.mx_scope == 0
        assert profile.gs_scope == 0

    def test_sequencing_implies_mutex(self):
        """Sequencing conflicts imply mutex."""
        profile, _ = compute_measures(SCENARIOS_DIR / "mixed/trust_travel.lp")
        assert profile.gs_scope > 0
        assert profile.mx_scope >= profile.gs_scope

    def test_mutex_without_sequencing_is_reversible(self):
        """Mutex without sequencing means reversible conflicts."""
        profile, _ = compute_measures(SCENARIOS_DIR / "p2_mutex/light_switch.lp")
        assert profile.mx_scope > 0
        assert profile.gs_scope == 0

    def test_delete_effects_block_reachability(self):
        """Delete effects must prevent false reachability claims.

        Regression test: the delete-relaxed fixpoint marks c as reachable
        because a and b are individually reachable. But {a,b} never coexist
        due to o1 deleting a, so o2 is never applicable and c is unreachable.
        """
        profile, _ = compute_measures(SCENARIOS_DIR / "edge_cases/delete_relaxation.lp")
        assert profile.ur_scope == 1  # c is unreachable
        assert profile.ur_struct == 1  # only c is unreachable (a, b both reachable)
        assert profile.mx_scope == 0  # no achievable goals to be mutex
        assert profile.gs_scope == 0


class TestTimingProfile:
    """Tests for per-phase timing breakdown."""

    def test_timing_returned(self):
        """compute_measures should return a TimingProfile alongside the MeasureProfile."""
        _, timing = compute_measures(SCENARIOS_DIR / "p1_unreachability/locked_door.lp")
        assert isinstance(timing, TimingProfile)
        assert timing.ground_s > 0
        assert timing.solve_s > 0
        assert timing.total_s > 0
        assert timing.translate_s == 0.0  # .lp input, no plasp

    def test_timing_as_dict(self):
        """as_dict should return all timing fields with correct keys."""
        _, timing = compute_measures(SCENARIOS_DIR / "edge_cases/single_goal.lp")
        d = timing.as_dict()
        assert set(d.keys()) == {
            "time_translate_s",
            "time_ground_s",
            "time_solve_s",
            "time_extract_s",
            "time_total_s",
        }
        assert all(isinstance(v, float) for v in d.values())

    def test_timing_field_names_matches_as_dict_keys(self):
        """field_names() and as_dict() must stay paired."""
        timing = TimingProfile(0.1, 0.2, 0.3, 0.4, 1.0)
        assert TimingProfile.field_names() == list(timing.as_dict().keys())
        assert TimingProfile.field_names() == [
            "time_translate_s",
            "time_ground_s",
            "time_solve_s",
            "time_extract_s",
            "time_total_s",
        ]
