# Planning Inconsistency Measures

ASP/Python implementation of diagnostic measures for classical planning problems.

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
profile = compute_measures("problem.pddl", domain_path="domain.pddl", horizon=20)
print(profile)           # (1,3,0,0,0,0)
print(profile.category)  # "2a"
print(profile.summary()) # Detailed breakdown

# From pre-translated ASP file
profile = compute_measures("problem.lp", horizon=20)

```

### Batch Benchmarking

Run measures on all problems in a benchmark directory:

```bash
# Via CLI
planning-measures batch benchmarks/diagnosis/ -o results/diagnosis.csv

# Via Python
python -c "
from planning_measures.batch import run_benchmark
run_benchmark('benchmarks/unsolve-ipc-2016/domains/FINAL/diagnosis', 'results/diagnosis.csv', timeout=60)
"
```

The runner auto-discovers domain/problem pairs using IPC naming conventions (`domain.pddl` + `prob*.pddl`, or numbered `dom01.pddl` + `prob01.pddl`). Output is a CSV with columns: `domain, problem, num_goals, num_props, num_operators, ur_scope, ur_struct, mx_scope, mx_struct, gs_scope, gs_struct, category, time_s, status`.

**Compatible IPC 2016 domains** (within 60s timeout): `diagnosis`, `pegsol-row5`, `bottleneck`, `cave-diving`, `document-transfer`. Other domains timeout due to grounding complexity. See the thesis (Ch5/Ch6) for details.

To run all compatible domains at once, use `skip_domains` to exclude known-incompatible ones:

```bash
python -c "
from planning_measures.batch import run_benchmark, KNOWN_INCOMPATIBLE
run_benchmark(
    'benchmarks/unsolve-ipc-2016/domains/FINAL',
    'results/ipc2016.csv',
    skip_domains=KNOWN_INCOMPATIBLE,
)
"
```

`KNOWN_INCOMPATIBLE` skips 9 domains that either fail with plasp (`:equality`) or timeout due to grounding complexity. Alternatively, pass `timeout=60` to `run_benchmark` to let them fail gracefully with `TIMEOUT` status in the CSV. Timeout is enforced by killing the child process with `SIGKILL`, which reliably terminates Clingo even during grounding.

### Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
thesis-planning-measures/
├── encodings/
│   ├── bridge_plasp.lp          # Maps plasp vocabulary to internal format
│   ├── planning.lp              # STRIPS problem representation
│   └── reachability.lp          # State exploration, witnesses, true reachability
├── planning_measures/           # Library package
│   ├── __init__.py              # Public API
│   ├── __main__.py              # Enables `python -m planning_measures`
│   ├── batch.py                 # Batch benchmark runner (CSV output)
│   ├── cli.py                   # CLI (planning-measures command)
│   ├── measures.py              # Core computation (single brave pass)
│   ├── pddl_preprocessor.py    # Strips action costs from PDDL for plasp
│   ├── profile.py               # MeasureProfile dataclass
│   └── solver.py                # Clingo wrapper (brave reasoning)
├── tests/
│   ├── pddl/                    # PDDL test cases
│   ├── scenarios/               # ASP test scenarios
│   ├── test_measures.py         # pytest: measure computation + hierarchy
│   └── test_plasp.py            # pytest: plasp pipeline + preprocessor
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Container definition
└── pyproject.toml               # Project config & dependencies
```

## Test Scenarios

| Scenario                           | Category | Expected Profile | Description                           |
| ---------------------------------- | -------- | ---------------- | ------------------------------------- |
| `edge_cases/coexisting_goals`      | Edge     | (0,0,0,0,0,0)    | Solvable, no conflicts                |
| `edge_cases/delete_relaxation`     | Edge     | (1,1,0,0,0,0)    | Delete effects block reachability     |
| `edge_cases/empty_goals`           | Edge     | (0,0,0,0,0,0)    | No goals defined                      |
| `edge_cases/horizon_sensitive`     | Edge     | (0,0,0,0,0,0)\*  | Chain requires sufficient horizon     |
| `edge_cases/negative_precondition` | Edge     | (1,1,0,0,0,0)    | Negative precondition blocks operator |
| `edge_cases/single_goal`           | Edge     | (0,0,0,0,0,0)    | Trivial single goal                   |
| `mixed/rival_alliances`            | Mixed    | (0,0,2,1,2,2)    | Two sequencing conflicts              |
| `mixed/trust_travel`               | Mixed    | (0,0,2,1,2,1)    | Asymmetric sequencing conflict        |
| `p1_unreachability/bank_vault`     | P1       | (1,7,0,0,0,0)    | Chain with multiple unreachable props |
| `p1_unreachability/locked_door`    | P1       | (1,3,0,0,0,0)    | Goal blocked by missing prerequisite  |
| `p2_mutex/light_switch`            | P2       | (0,0,2,1,0,0)    | Reversible toggle creates mutex       |
| `p2_mutex/traffic_light`           | P2       | (0,0,3,3,0,0)    | Three-way mutex clique                |

Profile format: `(ur_scope, ur_struct, mx_scope, mx_struct, gs_scope, gs_struct)`

The profile also exposes problem size metadata: `num_goals`, `num_props`, `num_operators`.

\*At default horizon=20. At horizon=2: `(1,1,0,0,0,0)` (insufficient depth).

## Architecture

Two independent layers:

- **Library** (`planning_measures/`): importable Python package with `compute_measures()`. Uses Python `logging` (no output unless caller configures a handler). Dependencies: clingo (Python), plasp (external).
- **CLI** (`planning_measures/cli.py`): `planning-measures` console script, installed via `pyproject.toml` entry point. Not imported by library or tests.

The PDDL pipeline:

1. **Preprocessing**: strips action costs from PDDL (irrelevant to inconsistency measures)
2. **plasp**: translates PDDL to lifted ASP representation
3. **Bridge encoding**: maps plasp vocabulary to internal predicates
4. **Brave reasoning**: Clingo explores state traces with `--enum-mode=brave`, computing the union of atoms across all answer sets
5. **Measure extraction**: Python computes P1 from set difference on `true_reachable`, P2/P3 from witness absence

## Configuration

Default horizon is 20 steps. Override via:

```python
profile = compute_measures("problem.pddl", domain_path="domain.pddl", horizon=100)
```

Timeouts are handled at the CLI/batch level (not the library API) using subprocess-based process killing.
