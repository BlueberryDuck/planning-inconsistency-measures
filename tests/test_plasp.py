"""
Tests for the PDDL translation pipeline and batch processing.

Run with: pytest tests/test_plasp.py -v
"""

import shutil
from pathlib import Path

import pytest

from planning_measures import compute_measures
from planning_measures.batch import find_pddl_pairs
from planning_measures.pddl_preprocessor import strip_costs

PDDL_DIR = Path(__file__).parent / "pddl"

requires_plasp = pytest.mark.skipif(
    shutil.which("plasp") is None,
    reason="plasp not installed",
)


@requires_plasp
class TestPlaspPipeline:
    """Tests for PDDL → plasp → measure computation."""

    def test_locked_door_pddl(self):
        """Locked Door via PDDL should match .lp scenario."""
        profile, timing = compute_measures(
            PDDL_DIR / "locked_door/problem01.pddl",
            domain_path=PDDL_DIR / "locked_door/domain.pddl",
        )
        assert profile.ur_scope == 1
        assert profile.mx_scope == 0
        assert profile.gs_scope == 0
        assert timing.translate_s > 0  # PDDL path exercises plasp translation

    def test_trust_travel_pddl(self):
        """Trust and Travel via PDDL should match .lp scenario."""
        profile, _ = compute_measures(
            PDDL_DIR / "trust_travel/problem01.pddl",
            domain_path=PDDL_DIR / "trust_travel/domain.pddl",
        )
        assert profile.mx_scope == 2
        assert profile.mx_struct == 1
        assert profile.gs_scope == 2
        assert profile.gs_struct == 1

    def test_domain_not_found(self):
        with pytest.raises(FileNotFoundError, match="Domain file not found"):
            compute_measures(
                PDDL_DIR / "locked_door/problem01.pddl",
                domain_path="nonexistent_domain.pddl",
            )

    def test_problem_not_found(self):
        with pytest.raises(FileNotFoundError, match="Problem file not found"):
            compute_measures(
                "nonexistent_problem.pddl",
                domain_path=PDDL_DIR / "locked_door/domain.pddl",
            )


class TestFindPddlPairs:
    """Tests for batch PDDL pair discovery."""

    def test_finds_pairs_in_test_dir(self):
        """Should discover domain/problem pairs in tests/pddl/."""
        pairs = find_pddl_pairs(PDDL_DIR)
        domains = {name for name, _, _ in pairs}
        assert "locked_door" in domains
        assert "trust_travel" in domains
        assert len(pairs) >= 2

    def test_returns_correct_structure(self):
        """Each pair should be (domain_name, domain_path, problem_path)."""
        pairs = find_pddl_pairs(PDDL_DIR)
        for name, domain_path, problem_path in pairs:
            assert isinstance(name, str)
            assert domain_path.exists()
            assert problem_path.exists()
            assert domain_path.name == "domain.pddl"

    def test_skip_domains(self):
        """Skipped domains should be excluded."""
        pairs = find_pddl_pairs(PDDL_DIR, skip_domains={"locked_door"})
        domains = {name for name, _, _ in pairs}
        assert "locked_door" not in domains
        assert "trust_travel" in domains


class TestPreprocessor:
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

    def test_strips_increase_effect(self):
        text = "(and (at ?x) (increase (total-cost) 1))"
        result = strip_costs(text)
        assert "increase" not in result
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
