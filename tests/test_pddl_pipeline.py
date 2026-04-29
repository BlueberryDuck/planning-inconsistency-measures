"""Unit tests for the PDDL pipeline: TranslatedProblem context manager + strip_costs.

These tests exercise the in-memory behavior. Tests that require the plasp
binary live in `test_plasp.py`.
"""

from pathlib import Path

import pytest

from planning_measures.pddl_pipeline import TranslatedProblem, strip_costs


class TestTranslatedProblemContextManager:
    def test_cleanup_callable_runs_on_exit(self):
        called: list[str] = []
        translated = TranslatedProblem(
            Path("/tmp/dummy.lp"),
            _cleanup=lambda: called.append("cleaned"),
        )

        with translated as tp:
            assert tp is translated

        assert called == ["cleaned"]

    def test_cleanup_runs_even_when_body_raises(self):
        called: list[str] = []
        translated = TranslatedProblem(
            Path("/tmp/dummy.lp"),
            _cleanup=lambda: called.append("cleaned"),
        )

        with pytest.raises(RuntimeError, match="boom"):
            with translated:
                raise RuntimeError("boom")

        assert called == ["cleaned"]


class TestStripCosts:
    """Tests for the PDDL cost-stripping preprocessor."""

    def test_strips_action_costs_requirement(self):
        text = "(:requirements :action-costs :strips :typing)"
        result = strip_costs(text)
        assert ":action-costs" not in result
        assert ":strips" in result

    def test_strips_functions_section(self):
        text = "(:functions (total-cost) - number)\n(:predicates (at ?x))"
        result = strip_costs(text)
        assert ":functions" not in result
        assert ":predicates" in result

    def test_strips_multiline_functions_block(self):
        text = """(:functions
    (total-cost)
    (road-length ?from ?to)
    - number
)
(:predicates (at ?x))"""
        result = strip_costs(text)
        assert ":functions" not in result
        assert "road-length" not in result
        assert "(:predicates (at ?x))" in result

    def test_strips_increase_effect(self):
        text = "(and (at ?x) (increase (total-cost) 1))"
        result = strip_costs(text)
        assert "increase" not in result
        assert "(at ?x)" in result

    def test_strips_decrease_effect(self):
        text = "(and (at ?x) (decrease (fuel ?v) 1))"
        result = strip_costs(text)
        assert "decrease" not in result
        assert "(at ?x)" in result

    def test_strips_function_assignments(self):
        text = "(= (road-length city1 city2) 22)"
        result = strip_costs(text)
        assert "road-length" not in result

    def test_strips_metric(self):
        text = "(:metric minimize (total-cost))"
        result = strip_costs(text)
        assert ":metric" not in result

    def test_preserves_non_cost_content(self):
        text = """(define (domain test)
(:requirements :strips :typing)
(:predicates (at ?x - location))
(:action move :parameters (?from ?to - location)
  :precondition (at ?from)
  :effect (and (at ?to) (not (at ?from)))))"""
        result = strip_costs(text)
        assert result.strip() == text.strip()

    def test_unmatched_paren_after_keyword_preserves_remainder(self):
        """Malformed PDDL: opener match without closing paren leaves tail intact."""
        text = "before (:metric minimize (total-cost) tail-without-close"
        result = strip_costs(text)
        assert "before " in result
        assert "tail-without-close" in result
