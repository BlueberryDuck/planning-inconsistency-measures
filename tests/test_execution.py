"""Tests for the execution module (timeout-protected compute)."""

from pathlib import Path

from planning_measures.execution import CSV_FIELDS, compute_with_timeout

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


def test_compute_with_timeout_ok_on_known_scenario():
    """In-process branch (timeout<=0) returns ok status with profile and timing."""
    result = compute_with_timeout(
        SCENARIOS_DIR / "p1_unreachability/locked_door.lp",
        domain=None,
        horizon=20,
        timeout=0,
    )
    assert result.status == "ok"
    assert result.profile is not None
    assert result.profile.as_tuple() == (1, 3, 0, 0, 0, 0)
    assert result.timing is not None
    assert result.elapsed_s > 0
    assert result.message is None


def test_to_csv_row_ok_composes_domain_problem_profile_timing_status():
    """OK row carries domain, problem stem, all profile fields, all timing fields, status='OK'."""
    result = compute_with_timeout(
        SCENARIOS_DIR / "p1_unreachability/locked_door.lp",
        domain=None,
        horizon=20,
        timeout=0,
    )
    row = result.to_csv_row(
        "p1_unreachability", SCENARIOS_DIR / "p1_unreachability/locked_door.lp"
    )
    assert row["domain"] == "p1_unreachability"
    assert row["problem"] == "locked_door"
    assert row["ur_scope"] == 1
    assert row["ur_struct"] == 3
    assert row["mx_scope"] == 0
    assert row["category"] == "2a"
    assert isinstance(row["time_total_s"], float)
    assert row["time_translate_s"] == 0.0
    assert row["status"] == "OK"


def test_to_csv_row_error_uses_empty_strings_and_error_status():
    """Non-OK rows have the same shape as OK rows but with empty measure/timing fields."""
    result = compute_with_timeout(
        Path("does/not/exist.lp"),
        domain=None,
        horizon=10,
        timeout=0,
    )
    row = result.to_csv_row("dom", Path("does/not/exist.lp"))
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
    result = compute_with_timeout(
        SCENARIOS_DIR / "p1_unreachability/locked_door.lp",
        domain=None,
        horizon=20,
        timeout=0,
    )
    assert list(result.to_csv_row("d", Path("p.lp")).keys()) == CSV_FIELDS


def test_status_label_maps_each_status():
    from planning_measures.execution import ExecutionResult

    ok = ExecutionResult("ok", None, None, None, 0.0)
    timeout = ExecutionResult("timeout", None, None, None, 1.5)
    err = ExecutionResult("error", None, None, "RuntimeError: boom", 0.0)
    assert ok.status_label() == "OK"
    assert timeout.status_label() == "TIMEOUT"
    assert err.status_label() == "ERROR: RuntimeError: boom"


def test_compute_with_timeout_error_on_missing_problem():
    """Compute failure surfaces as status='error' with a non-empty message."""
    result = compute_with_timeout(
        Path("does/not/exist.lp"),
        domain=None,
        horizon=10,
        timeout=0,
    )
    assert result.status == "error"
    assert result.profile is None
    assert result.timing is None
    assert result.message
    assert (
        "FileNotFoundError" in result.message or "not found" in result.message.lower()
    )
    assert result.elapsed_s >= 0
