"""Unit tests for the PDDL pipeline: TranslatedProblem context manager + Translate.

These tests exercise the in-memory behavior of `TranslatedProblem`. Tests
that require the plasp binary live in `test_plasp.py`.
"""

from pathlib import Path

import pytest

from planning_measures.pddl_pipeline import TranslatedProblem


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
