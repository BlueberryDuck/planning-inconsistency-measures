"""
Tests for PDDL to ASP translator.

Run with: pytest tests/test_translator.py -v
"""

import pytest
import tempfile
from pathlib import Path

from pddl import parse_domain, parse_problem

from planning_measures import compute_measures, translate_pddl
from planning_measures.translator import translate


PDDL_DIR = Path(__file__).parent / "pddl"

# Expected profiles after translation
EXPECTED_PROFILES = {
    "locked_door": (1, 3, 0, 0, 0, 0),
    "trust_travel": (0, 0, 2, 1, 2, 1),
}


class TestTranslatePddlAPI:
    """Test the public translate_pddl function."""

    def test_returns_asp_string(self):
        output = translate_pddl(
            PDDL_DIR / "trust_travel/domain.pddl",
            PDDL_DIR / "trust_travel/problem01.pddl",
        )
        assert isinstance(output, str)
        assert "init(" in output
        assert "goal(" in output

    def test_writes_to_file(self, tmp_path):
        output_file = tmp_path / "output.lp"
        translate_pddl(
            PDDL_DIR / "locked_door/domain.pddl",
            PDDL_DIR / "locked_door/problem01.pddl",
            output_file,
        )
        assert output_file.exists()
        assert "goal(" in output_file.read_text()

    def test_domain_not_found(self):
        with pytest.raises(FileNotFoundError, match="Domain file not found"):
            translate_pddl("nonexistent.pddl", PDDL_DIR / "locked_door/problem01.pddl")

    def test_problem_not_found(self):
        with pytest.raises(FileNotFoundError, match="Problem file not found"):
            translate_pddl(PDDL_DIR / "locked_door/domain.pddl", "nonexistent.pddl")


class TestTranslatorOutput:
    """Test that translator produces valid ASP."""

    def test_locked_door_translation(self):
        domain = parse_domain(PDDL_DIR / "locked_door/domain.pddl")
        problem = parse_problem(PDDL_DIR / "locked_door/problem01.pddl")
        output = translate(domain, problem)

        assert "goal(" in output
        assert "precond(" in output or "add(" in output

    def test_trust_travel_translation(self):
        domain = parse_domain(PDDL_DIR / "trust_travel/domain.pddl")
        problem = parse_problem(PDDL_DIR / "trust_travel/problem01.pddl")
        output = translate(domain, problem)

        assert "goal(partnership)" in output
        assert "goal(opportunity)" in output


@pytest.mark.parametrize("scenario,expected", EXPECTED_PROFILES.items())
def test_translated_measures(scenario: str, expected: tuple):
    """Translated PDDL should produce correct measures."""
    domain = parse_domain(PDDL_DIR / f"{scenario}/domain.pddl")
    problem = parse_problem(PDDL_DIR / f"{scenario}/problem01.pddl")
    output = translate(domain, problem)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False) as f:
        f.write(output)
        f.flush()
        profile = compute_measures(f.name)

    assert profile.as_tuple() == expected
