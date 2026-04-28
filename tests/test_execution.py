"""Tests for the execution module (timeout-protected compute)."""

from pathlib import Path

from planning_measures import MeasureResult
from planning_measures.execution import (
    CSV_FIELDS,
    ExecutionResult,
    compute_with_timeout,
)

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


def test_compute_with_timeout_ok_on_known_scenario():
    """In-process branch (timeout<=0) returns ok status carrying a MeasureResult."""
    execution = compute_with_timeout(
        SCENARIOS_DIR / "p1_unreachability/locked_door.lp",
        domain=None,
        horizon=20,
        timeout=0,
    )
    assert execution.status == "ok"
    assert isinstance(execution.result, MeasureResult)
    assert execution.result.profile.as_tuple() == (1, 3, 0, 0, 0, 0)
    assert execution.elapsed_s > 0
    assert execution.message is None


def test_to_csv_row_ok_composes_domain_problem_size_profile_timing_status():
    """OK row carries domain, problem stem, size, profile, timing fields, status='OK'."""
    execution = compute_with_timeout(
        SCENARIOS_DIR / "p1_unreachability/locked_door.lp",
        domain=None,
        horizon=20,
        timeout=0,
    )
    row = execution.to_csv_row(
        "p1_unreachability", SCENARIOS_DIR / "p1_unreachability/locked_door.lp"
    )
    assert row["domain"] == "p1_unreachability"
    assert row["problem"] == "locked_door"
    assert row["ur_scope"] == 1
    assert row["ur_struct"] == 3
    assert row["mx_scope"] == 0
    assert row["category"] == "2a"
    assert isinstance(row["num_goals"], int)
    assert isinstance(row["time_total_s"], float)
    assert row["time_translate_s"] == 0.0
    assert row["status"] == "OK"


def test_to_csv_row_error_uses_empty_strings_and_error_status():
    """Non-OK rows have the same shape as OK rows but with empty measure/timing fields."""
    execution = compute_with_timeout(
        Path("does/not/exist.lp"),
        domain=None,
        horizon=10,
        timeout=0,
    )
    row = execution.to_csv_row("dom", Path("does/not/exist.lp"))
    assert row["domain"] == "dom"
    assert row["problem"] == "exist"
    for name in (
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
        "time_translate_s",
        "time_ground_s",
        "time_solve_s",
        "time_extract_s",
        "time_total_s",
    ):
        assert row[name] == "", f"expected empty for {name}, got {row[name]!r}"
    assert row["status"].startswith("ERROR: ")
    assert "FileNotFoundError" in row["status"] or "not found" in row["status"].lower()


def test_csv_fields_matches_order_and_to_csv_row_keys():
    """CSV_FIELDS pins the column order; to_csv_row must produce exactly those keys."""
    assert CSV_FIELDS == [
        "domain",
        "problem",
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
        "time_translate_s",
        "time_ground_s",
        "time_solve_s",
        "time_extract_s",
        "time_total_s",
        "status",
    ]
    execution = compute_with_timeout(
        SCENARIOS_DIR / "p1_unreachability/locked_door.lp",
        domain=None,
        horizon=20,
        timeout=0,
    )
    assert list(execution.to_csv_row("d", Path("p.lp")).keys()) == CSV_FIELDS


def test_status_label_maps_each_status():
    ok = ExecutionResult("ok", None, None, 0.0)
    timeout = ExecutionResult("timeout", None, None, 1.5)
    err = ExecutionResult("error", None, "RuntimeError: boom", 0.0)
    assert ok.status_label() == "OK"
    assert timeout.status_label() == "TIMEOUT"
    assert err.status_label() == "ERROR: RuntimeError: boom"


def test_to_csv_row_status_collapses_multiline_errors():
    """Multiline error messages (e.g. from plasp stderr) collapse to a single line in CSV."""
    err = ExecutionResult(
        "error",
        None,
        "RuntimeError: plasp failed:\nproblem.pddl:3:5: error\ninfo: try --parsing-mode",
        0.0,
    )
    row = err.to_csv_row("dom", Path("p.pddl"))
    assert "\n" not in row["status"]
    assert "\r" not in row["status"]
    assert (
        row["status"]
        == "ERROR: RuntimeError: plasp failed: problem.pddl:3:5: error info: try --parsing-mode"
    )


def test_compute_with_timeout_error_on_missing_problem():
    """Compute failure surfaces as status='error' with a non-empty message."""
    execution = compute_with_timeout(
        Path("does/not/exist.lp"),
        domain=None,
        horizon=10,
        timeout=0,
    )
    assert execution.status == "error"
    assert execution.result is None
    assert execution.message
    assert (
        "FileNotFoundError" in execution.message
        or "not found" in execution.message.lower()
    )
    assert execution.elapsed_s >= 0
