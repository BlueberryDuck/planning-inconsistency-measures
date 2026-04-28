"""Tests for profile dataclasses: MeasureProfile, ProblemSize, MeasureResult, TimingProfile."""

import pytest

from planning_measures.profile import (
    MeasureProfile,
    MeasureResult,
    ProblemSize,
    TimingProfile,
)


class TestProblemSize:
    def test_stores_cardinalities(self):
        size = ProblemSize(num_goals=3, num_props=10, num_operators=7)
        assert size.num_goals == 3
        assert size.num_props == 10
        assert size.num_operators == 7

    def test_is_frozen(self):
        size = ProblemSize(num_goals=1, num_props=2, num_operators=3)
        with pytest.raises((AttributeError, Exception)):
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
        with pytest.raises((AttributeError, Exception)):
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
