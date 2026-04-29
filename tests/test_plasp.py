"""
Tests for the PDDL translation pipeline and batch processing.

Run with: pytest tests/test_plasp.py -v
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from planning_measures import compute_measures
from planning_measures.pddl_pipeline import (
    TranslatedProblem,
    translate_pddl,
)

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
        result = compute_measures(
            PDDL_DIR / "locked_door/problem01.pddl",
            domain_path=PDDL_DIR / "locked_door/domain.pddl",
        )
        assert result.profile.ur_scope == 1
        assert result.profile.mx_scope == 0
        assert result.profile.gs_scope == 0
        assert result.timing.translate_s > 0  # PDDL path exercises plasp translation

    def test_trust_travel_pddl(self):
        """Trust and Travel via PDDL should match .lp scenario."""
        result = compute_measures(
            PDDL_DIR / "trust_travel/problem01.pddl",
            domain_path=PDDL_DIR / "trust_travel/domain.pddl",
        )
        assert result.profile.mx_scope == 2
        assert result.profile.mx_struct == 1
        assert result.profile.gs_scope == 2
        assert result.profile.gs_struct == 1

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


@requires_plasp
class TestTranslatePddl:
    """Tests for the Translate context manager."""

    def test_yields_translated_problem_with_needs_bridge_true(self):
        with translate_pddl(
            PDDL_DIR / "locked_door/domain.pddl",
            PDDL_DIR / "locked_door/problem01.pddl",
        ) as translated:
            assert isinstance(translated, TranslatedProblem)
            assert translated.needs_bridge is True
            assert translated.translate_s > 0
            assert translated.path.exists()

    def test_raises_and_cleans_up_temp_dir_on_plasp_failure(
        self, tmp_path, monkeypatch
    ):
        bad_domain = tmp_path / "bad_domain.pddl"
        bad_domain.write_text("(this is not valid pddl)")
        bad_problem = tmp_path / "bad_problem.pddl"
        bad_problem.write_text("(neither is this)")

        created_dirs: list[str] = []
        real_mkdtemp = tempfile.mkdtemp

        def tracked_mkdtemp(*args, **kwargs):
            d = real_mkdtemp(*args, **kwargs)
            created_dirs.append(d)
            return d

        monkeypatch.setattr(tempfile, "mkdtemp", tracked_mkdtemp)

        with pytest.raises(RuntimeError, match="plasp translation failed"):
            translate_pddl(bad_domain, bad_problem)

        assert created_dirs, "expected translate_pddl to call tempfile.mkdtemp"
        for d in created_dirs:
            assert not Path(d).exists(), f"temp dir {d} not cleaned up"
