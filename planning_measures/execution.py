"""Timeout-protected execution of measure computation.

Owns the subprocess driver, the discriminated `ExecutionResult` outcome,
and CSV row composition. CLI and batch are thin formatters over it.
"""

import multiprocessing as mp
import time
from dataclasses import dataclass
from multiprocessing.queues import Queue
from pathlib import Path
from typing import Literal

from .measures import compute_measures
from .profile import MeasureProfile, TimingProfile

Status = Literal["ok", "timeout", "error"]

CSV_FIELDS: list[str] = [
    "domain",
    "problem",
    *MeasureProfile.field_names(),
    *TimingProfile.field_names(),
    "status",
]


@dataclass(frozen=True)
class ExecutionResult:
    status: Status
    profile: MeasureProfile | None
    timing: TimingProfile | None
    message: str | None
    elapsed_s: float

    @classmethod
    def ok(
        cls, profile: MeasureProfile, timing: TimingProfile, elapsed_s: float
    ) -> "ExecutionResult":
        return cls("ok", profile, timing, None, elapsed_s)

    @classmethod
    def timeout(cls, elapsed_s: float) -> "ExecutionResult":
        return cls("timeout", None, None, None, elapsed_s)

    @classmethod
    def error(cls, message: str, elapsed_s: float) -> "ExecutionResult":
        return cls("error", None, None, message, elapsed_s)

    def status_label(self) -> str:
        """Human-readable status string used by CLI stderr and CSV `status` column."""
        if self.status == "ok":
            return "OK"
        if self.status == "timeout":
            return "TIMEOUT"
        return f"ERROR: {self.message}"

    def unwrap(self) -> tuple[MeasureProfile, TimingProfile]:
        """Return (profile, timing) when status=='ok'; raise otherwise."""
        if self.status != "ok" or self.profile is None or self.timing is None:
            raise RuntimeError(f"unwrap on non-ok result: {self.status_label()}")
        return self.profile, self.timing

    def to_csv_row(self, domain: str, problem: Path) -> dict:
        """Compose a CSV row: domain + problem stem + measure fields + timing fields + status."""
        row: dict = {"domain": domain, "problem": problem.stem}
        if self.status == "ok" and self.profile is not None and self.timing is not None:
            row.update(self.profile.as_dict())
            row.update(self.timing.as_dict())
        else:
            for name in MeasureProfile.field_names():
                row[name] = ""
            for name in TimingProfile.field_names():
                row[name] = ""
        row["status"] = self.status_label()
        return row


def _worker(queue: Queue, problem: str, domain: str | None, horizon: int) -> None:
    """Child-process entry: compute and ship result through the queue."""
    try:
        profile, timing = compute_measures(problem, domain_path=domain, horizon=horizon)
        queue.put(("ok", (profile, timing)))
    except Exception as e:
        queue.put(("error", f"{type(e).__name__}: {e}"))


def compute_with_timeout(
    problem: str | Path,
    domain: str | Path | None,
    horizon: int,
    timeout: int,
) -> ExecutionResult:
    """Timeout-protected compute. timeout<=0 runs in-process; otherwise subprocess + SIGKILL."""
    start = time.monotonic()

    def elapsed() -> float:
        return time.monotonic() - start

    if timeout <= 0:
        try:
            profile, timing = compute_measures(
                problem, domain_path=domain, horizon=horizon
            )
        except Exception as e:
            return ExecutionResult.error(f"{type(e).__name__}: {e}", elapsed())
        return ExecutionResult.ok(profile, timing, elapsed())

    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    proc = ctx.Process(
        target=_worker,
        args=(queue, str(problem), str(domain) if domain else None, horizon),
    )
    proc.start()
    proc.join(timeout=timeout)

    if proc.is_alive():
        proc.kill()
        proc.join()
        return ExecutionResult.timeout(elapsed())

    try:
        status, value = queue.get_nowait()
    except Exception:
        return ExecutionResult.error("worker exited without result", elapsed())

    if status == "ok":
        profile, timing = value
        return ExecutionResult.ok(profile, timing, elapsed())
    return ExecutionResult.error(value, elapsed())
