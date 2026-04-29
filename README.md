# Planning Inconsistency Measures

ASP/Python implementation of diagnostic measures for classical planning problems.

This repository implements the Master's thesis _Inconsistency Measurement for Classical Planning Problems_ by Sebastian Bunge (FernUniversität in Hagen, 2026). Thesis sources: [BlueberryDuck/thesis-inconsistency-planning](https://github.com/BlueberryDuck/thesis-inconsistency-planning).

## Overview

Computes three measures that quantify goal conflicts in unsolvable planning problems:

| Measure | Name           | Description                                     |
| ------- | -------------- | ----------------------------------------------- |
| P1      | Unreachability | Goals that cannot be reached                    |
| P2      | Mutex          | Achievable goals that can never coexist         |
| P3      | Sequencing     | Goal pairs where achieving one blocks the other |

Each measure has `scope` (goals involved) and `struct` (conflict count) variants.

## Installation

```bash
# Docker (recommended)
docker compose build

# Or local install (requires plasp and clingo)
pip install -e ".[dev]"
```

## Usage

### CLI

```bash
# Single ASP scenario
planning-measures compute tests/scenarios/p1_unreachability/locked_door.lp

# PDDL problem
planning-measures compute -d domain.pddl problem.pddl

# Custom horizon and timeout
planning-measures compute -d domain.pddl problem.pddl -H 30 -t 60

# Batch run (outputs CSV)
planning-measures batch benchmarks/diagnosis/ -o results/diagnosis.csv

# Help
planning-measures -h
planning-measures compute -h
```

With Docker: prefix commands with `./run.sh` (e.g., `./run.sh planning-measures compute ...`).

### Library API

```python
from planning_measures import compute_measures

# From PDDL files (uses plasp for translation)
result = compute_measures("problem.pddl", domain_path="domain.pddl", horizon=20)
print(result.profile)            # (1,3,0,0,0,0)
print(result.profile.category)   # "2a"
print(result.size.num_goals)     # Problem size cardinalities
print(result.timing.ground_s)    # Grounding time in seconds
print(result.summary())          # Human-readable breakdown

# From pre-translated ASP file
result = compute_measures("problem.lp", horizon=20)
```

`compute_measures` returns a `MeasureResult` containing the diagnostic `MeasureProfile`, the input's `ProblemSize`, and a `TimingProfile`.

Timeout-protected execution from Python uses `compute_with_timeout`:

```python
from planning_measures import compute_with_timeout

execution = compute_with_timeout("problem.pddl", "domain.pddl", horizon=20, timeout=60)
if execution.status == "ok":
    result = execution.unwrap()
    print(result.profile, result.size, result.timing)
elif execution.status == "timeout":
    print(f"timed out after {execution.elapsed_s:.1f}s")
else:
    print(f"error: {execution.message}")
```

Pure extraction is also exposed for callers wiring their own pipeline:

```python
from planning_measures import BraveOutcome, extract_measures, extract_problem_size

outcome = BraveOutcome(goals=..., props=..., operators=..., true_reachable=...,
                      coexist_witness=..., g2_after_g1_witness=...)
profile = extract_measures(outcome)
size = extract_problem_size(outcome)
```

### Batch Benchmarking

Run measures on all problems in a benchmark directory:

```bash
# Via CLI
planning-measures batch benchmarks/diagnosis/ -o results/diagnosis.csv

# Via Python
python -c "
from planning_measures.batch import run_benchmark
run_benchmark('benchmarks/unsolve-ipc-2016/domains/FINAL/diagnosis', 'results/diagnosis.csv', timeout=120)
"
```

The runner auto-discovers domain/problem pairs via `benchmark_layout.discover`, which supports `domain.pddl` + `prob*.pddl`, numbered `dom01.pddl` + `prob01.pddl` / `satprob01.pddl`, and `domain_<name>.pddl` + `<name>.pddl` (Eriksson) layouts. Output is a CSV with columns: `domain, problem, num_goals, num_props, num_operators, ur_scope, ur_struct, mx_scope, mx_struct, gs_scope, gs_struct, category, time_translate_s, time_ground_s, time_solve_s, time_extract_s, time_total_s, status`.

**Compatible IPC 2016 domains** (within 120s timeout): `diagnosis`, `pegsol-row5`, `bottleneck`, `cave-diving`, `document-transfer`, `chessboard-pebbling`. The `3unsat` domain from the Eriksson benchmarks is also compatible. Other domains timeout due to grounding complexity. See the thesis for details.

To run all compatible domains at once, use `skip_domains` to exclude known-incompatible ones:

```bash
python -c "
from planning_measures.batch import run_benchmark
from planning_measures.benchmark_layout import KNOWN_INCOMPATIBLE
run_benchmark(
    'benchmarks/unsolve-ipc-2016/domains/FINAL',
    'results/ipc2016.csv',
    skip_domains=KNOWN_INCOMPATIBLE,
)
"
```

`KNOWN_INCOMPATIBLE` skips 9 domains that either fail with plasp (`:equality`) or timeout due to grounding complexity. Alternatively, pass `timeout=120` to `run_benchmark` to let them fail gracefully with `TIMEOUT` status in the CSV. Timeout is enforced by killing the child process with `SIGKILL`, which reliably terminates Clingo even during grounding.

### Running Tests

```bash
pytest tests/ -v
```

## Architecture

Two layers:

- **Library** (`planning_measures/`): importable Python package with `compute_measures()` and `compute_with_timeout()`. `compute_measures()` returns a `MeasureResult` and raises on failure; `compute_with_timeout()` returns a discriminated `ExecutionResult` carrying that `MeasureResult`. Uses Python `logging` (no output unless caller configures a handler). Dependencies: clingo (Python), plasp (external).
- **CLI** (`planning_measures/cli.py`): `planning-measures` console script, installed via `pyproject.toml` entry point. Not imported by library or tests.

The PDDL pipeline:

1. **Preprocess** (`pddl_pipeline.strip_costs`): strips action costs from PDDL (irrelevant to inconsistency measures)
2. **Translate** (`pddl_pipeline.translate_pddl`): runs plasp to translate PDDL to lifted ASP, yielding a context-managed `TranslatedProblem` (path + `needs_bridge` + `translate_s`)
3. **Bridge encoding**: `bridge_plasp.lp` maps plasp vocabulary to internal predicates; loaded by Brave reasoning iff `translated.needs_bridge`
4. **Brave reasoning** (`brave.run_brave_reasoning`): Clingo grounds and solves with `--enum-mode=brave`, filters by a private atom vocabulary, and returns a `BraveReasoningResult` (a `BraveOutcome` plus `ground_s`/`solve_s`)
5. **Extraction** (`extraction.extract_measures`): pure set algebra over `BraveOutcome` — P1 from set difference on `true_reachable`, P2/P3 from witness absence

Each phase is individually timed (`TimingProfile`), with grounding and solving measured separately to identify bottlenecks. The typed seams — `TranslatedProblem` from Translate, `BraveOutcome` from Brave reasoning — keep each step pure and independently testable. Timeouts and CSV row composition live in `planning_measures/execution.py`, which both the CLI and batch runner use; timeout enforcement uses a subprocess + SIGKILL so Clingo can be killed reliably even during grounding.

## Test Scenarios

Twelve hand-crafted ASP scenarios cover P1 (unreachability), P2 (mutex), P3 (sequencing), mixed conflicts, and edge cases. Each scenario has an expected `MeasureProfile` asserted by `tests/test_measures.py`.

Profile format: `(ur_scope, ur_struct, mx_scope, mx_struct, gs_scope, gs_struct)`. Problem-size metadata (`num_goals`, `num_props`, `num_operators`) is carried alongside on `MeasureResult.size`.

See [tests/scenarios/README.md](tests/scenarios/README.md) for the full catalog, expected profiles, and the scenario file format.

## Project Structure

```
planning-inconsistency-measures/
├── encodings/
│   ├── bridge_plasp.lp          # Maps plasp vocabulary to internal format
│   ├── planning.lp              # STRIPS problem representation
│   └── reachability.lp          # State exploration, witnesses, true reachability
├── planning_measures/           # Library package
│   ├── __init__.py              # Public API
│   ├── __main__.py              # Enables `python -m planning_measures`
│   ├── batch.py                 # Batch benchmark runner (CSV output)
│   ├── benchmark_layout.py      # Benchmark discovery: discover() + KNOWN_INCOMPATIBLE
│   ├── brave.py                 # Brave reasoning: BraveOutcome, BraveReasoningResult, run_brave_reasoning
│   ├── cli.py                   # CLI (planning-measures command)
│   ├── execution.py             # Timeout-protected compute + ExecutionResult + CSV row composition
│   ├── extraction.py            # Pure set-algebra extraction over BraveOutcome (P1/P2/P3)
│   ├── measures.py              # Pipeline orchestrator (translate -> brave reasoning -> extract)
│   ├── pddl_pipeline.py         # Preprocess (strip_costs) + Translate (TranslatedProblem, translate_pddl)
│   └── profile.py               # MeasureProfile, ProblemSize, TimingProfile, MeasureResult
├── results/                     # Benchmark experiment outputs (see results/README.md)
├── tests/
│   ├── pddl/                    # PDDL test cases (see tests/pddl/README.md)
│   ├── scenarios/               # ASP test scenarios (see tests/scenarios/README.md)
│   ├── test_benchmark_layout.py # pytest: discover() over synthetic IPC layouts
│   ├── test_brave.py            # pytest: run_brave_reasoning + BraveReasoningResult
│   ├── test_execution.py        # pytest: compute_with_timeout + ExecutionResult
│   ├── test_extraction.py       # pytest: pure extraction (no Clingo)
│   ├── test_measures.py         # pytest: pipeline integration + scenario profiles
│   ├── test_pddl_pipeline.py    # pytest: TranslatedProblem context manager + strip_costs
│   ├── test_plasp.py            # pytest: translate_pddl end-to-end (requires plasp)
│   └── test_profile.py          # pytest: profile / size / result dataclasses
├── CITATION.cff                 # Citation metadata
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Container definition
├── LICENSE                      # MIT License
└── pyproject.toml               # Project config & dependencies
```

Subdirectory READMEs: [`encodings/`](encodings) (inline comments), [`tests/scenarios/README.md`](tests/scenarios/README.md), [`tests/pddl/README.md`](tests/pddl/README.md), [`results/README.md`](results/README.md).
