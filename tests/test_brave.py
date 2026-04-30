"""Tests for the Brave reasoning step.

`run_brave_reasoning` consumes a `TranslatedProblem` and produces a typed
`BraveReasoningResult` (a `BraveOutcome` plus per-phase wall-clock timing).
The atom vocabulary is a private detail of this module, not a caller concern.
"""

from pathlib import Path

import pytest

from planning_measures.brave import BraveReasoningResult, run_brave_reasoning
from planning_measures.extraction import BraveOutcome
from planning_measures.pddl_pipeline import TranslatedProblem

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


class TestRunBraveReasoning:
    def test_returns_result_with_outcome_for_known_scenario(self):
        translated = TranslatedProblem(SCENARIOS_DIR / "edge_cases/single_goal.lp")
        with translated as tp:
            result = run_brave_reasoning(tp, horizon=5)

        assert isinstance(result, BraveReasoningResult)
        assert isinstance(result.outcome, BraveOutcome)
        assert "ready" in result.outcome.goals
        assert result.ground_s >= 0
        assert result.solve_s >= 0

    def test_unsat_problem_raises_runtime_error(self):
        translated = TranslatedProblem(SCENARIOS_DIR / "edge_cases/unsatisfiable.lp")
        with pytest.raises(RuntimeError, match="ASP solving failed"):
            with translated as tp:
                run_brave_reasoning(tp, horizon=5)
