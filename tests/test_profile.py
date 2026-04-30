"""Tests for profile dataclasses: MeasureProfile, ProblemSize, MeasureResult, TimingProfile."""

import pytest

from planning_measures.profile import (
    MeasureProfile,
    MeasureResult,
    ProblemSize,
    TimingProfile,
)


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
        """field_names locks the schema for CSV row composition (measures only)."""
        assert MeasureProfile.field_names() == [
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
        p = MeasureProfile(1, 3, 0, 0, 0, 0)
        d = p.as_dict()
        assert list(d.keys()) == MeasureProfile.field_names()
        assert d["ur_scope"] == 1
        assert d["ur_struct"] == 3
        assert d["category"] == "2a"


class TestTimingProfile:
    """Tests for TimingProfile dataclass shape (no Clingo)."""

    def test_as_dict_keyed_by_field_names(self):
        """as_dict should return all timing fields with correct keys."""
        timing = TimingProfile(0.1, 0.2, 0.3, 0.4, 1.0)
        d = timing.as_dict()
        assert set(d.keys()) == {
            "time_translate_s",
            "time_ground_s",
            "time_solve_s",
            "time_extract_s",
            "time_total_s",
        }
        assert all(isinstance(v, float) for v in d.values())

    def test_field_names_matches_as_dict_keys(self):
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


class TestProblemSize:
    def test_stores_cardinalities(self):
        size = ProblemSize(num_goals=3, num_props=10, num_operators=7)
        assert size.num_goals == 3
        assert size.num_props == 10
        assert size.num_operators == 7

    def test_is_frozen(self):
        size = ProblemSize(num_goals=1, num_props=2, num_operators=3)
        with pytest.raises(AttributeError):
            size.num_goals = 99  # type: ignore[misc]

    def test_field_names_locks_csv_order(self):
        assert ProblemSize.field_names() == ["num_goals", "num_props", "num_operators"]

    def test_as_dict_keyed_by_field_names(self):
        size = ProblemSize(num_goals=4, num_props=8, num_operators=2)
        d = size.as_dict()
        assert list(d.keys()) == ProblemSize.field_names()
        assert d == {"num_goals": 4, "num_props": 8, "num_operators": 2}

    def test_no_implicit_defaults(self):
        """Cardinalities are required; a profile that doesn't know its size shouldn't construct."""
        with pytest.raises(TypeError):
            ProblemSize()  # type: ignore[call-arg]


class TestMeasureResult:
    def test_bundles_profile_size_timing(self):
        profile = MeasureProfile(1, 3, 0, 0, 0, 0)
        size = ProblemSize(num_goals=2, num_props=5, num_operators=4)
        timing = TimingProfile(0.1, 0.2, 0.3, 0.4, 1.0)

        result = MeasureResult(profile=profile, size=size, timing=timing)

        assert result.profile is profile
        assert result.size is size
        assert result.timing is timing

    def test_is_frozen(self):
        result = MeasureResult(
            profile=MeasureProfile(0, 0, 0, 0, 0, 0),
            size=ProblemSize(0, 0, 0),
            timing=TimingProfile(),
        )
        with pytest.raises(AttributeError):
            result.profile = MeasureProfile(1, 1, 1, 1, 1, 1)  # type: ignore[misc]

    def test_summary_renders_profile_size_and_category(self):
        result = MeasureResult(
            profile=MeasureProfile(1, 3, 0, 0, 0, 0),
            size=ProblemSize(num_goals=2, num_props=5, num_operators=4),
            timing=TimingProfile(),
        )
        text = result.summary()

        assert "(1,3,0,0,0,0)" in text
        assert "Category: 2a" in text
        assert "2 goals" in text
        assert "5 propositions" in text
        assert "4 operators" in text
        assert "P1 Unreachability" in text
        assert "P2 Mutex" in text
        assert "P3 Sequencing" in text
        assert "Unreachable goals: 1" in text
        assert "Total unreachable propositions: 3" in text
