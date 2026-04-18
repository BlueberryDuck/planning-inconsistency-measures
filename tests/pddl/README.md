# PDDL Test Fixtures

_Part of [Planning Inconsistency Measures](../../README.md)._

PDDL versions of two hand-written ASP scenarios (`locked_door`, `trust_travel`), used by `tests/test_plasp.py::TestPlaspPipeline` to cross-validate the PDDL → plasp → ASP pipeline against the corresponding `.lp` files under [`tests/scenarios/`](../scenarios/README.md).

Each subdirectory follows IPC naming (`domain.pddl` + `problem01.pddl`). Tests are gated on `plasp` being installed (see the `requires_plasp` marker in `test_plasp.py`).
