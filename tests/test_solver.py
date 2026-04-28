"""Tests for the Clingo solver wrapper.

The solver is generic: it takes a `keep_atoms` filter and returns a bucket
dict keyed by atom name. Domain knowledge (which atom names matter) lives in
`extraction.KEEP_ATOMS`, not here.
"""

from pathlib import Path

import pytest

from planning_measures.solver import solve_brave

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


class TestSolveBraveBuckets:
    def test_returns_buckets_keyed_by_atom_name(self):
        buckets, t_ground, t_solve = solve_brave(
            SCENARIOS_DIR / "edge_cases/single_goal.lp",
            horizon=5,
            keep_atoms=frozenset({"goal", "prop", "operator", "true_reachable"}),
        )

        assert isinstance(buckets, dict)
        assert "goal" in buckets
        assert ("ready",) in buckets["goal"]
        assert t_ground >= 0
        assert t_solve >= 0

    def test_atoms_outside_filter_are_dropped(self):
        """The bucket dict only contains atoms named in `keep_atoms`."""
        buckets, _, _ = solve_brave(
            SCENARIOS_DIR / "edge_cases/single_goal.lp",
            horizon=5,
            keep_atoms=frozenset({"goal"}),
        )

        # 'goal' kept, everything else absent
        assert "goal" in buckets
        assert "prop" not in buckets
        assert "operator" not in buckets
        assert "holds" not in buckets

    def test_unsat_problem_raises_runtime_error(self):
        """Solver owns the satisfiability check end-to-end."""
        with pytest.raises(RuntimeError, match="ASP solving failed"):
            solve_brave(
                SCENARIOS_DIR / "edge_cases/unsatisfiable.lp",
                horizon=5,
                keep_atoms=frozenset({"goal"}),
            )
