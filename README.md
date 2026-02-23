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

# Or local install
pip install -e ".[dev]"
```

## Usage

### Interactive Mode

```bash
python cli.py
```

Provides a menu-driven interface for:

- Computing measures for single problems
- Running test scenarios
- Batch processing directories
- Translating PDDL files

### Library API

```python
from planning_measures import compute_measures, translate_pddl

# Compute measures from ASP problem
profile = compute_measures("problem.lp", horizon=20)
print(profile)           # (1,3,0,0,0,0)
print(profile.category)  # "2a"
print(profile.summary()) # Detailed breakdown

# Translate PDDL to ASP
asp_text = translate_pddl("domain.pddl", "problem.pddl")
```

### Running Tests

```bash
pytest tests/ -v
```

### PDDL Translation

Use the interactive CLI (`python cli.py` → option 4) or the library API:

```python
from planning_measures import translate_pddl, batch_translate

# Single file
asp_text = translate_pddl("domain.pddl", "problem.pddl", "output.lp")

# Batch translation
batch_translate("~/benchmarks/ipc2016", "benchmarks/translated", workers=4)
```

## Project Structure

```
thesis-planning-measures/
├── encodings/
│   ├── planning.lp              # STRIPS problem representation
│   └── reachability.lp          # Reachability, witnesses, true reachability
├── planning_measures/           # Library package
│   ├── __init__.py              # Public API
│   ├── batch_translator.py      # Batch PDDL translator
│   ├── measures.py              # Core computation (single brave pass)
│   ├── profile.py               # MeasureProfile dataclass
│   ├── solver.py                # Clingo wrapper (brave reasoning)
│   └── translator.py            # PDDL to ASP translator
├── tests/
│   ├── pddl/                    # PDDL test cases
│   ├── scenarios/               # ASP test scenarios
│   ├── test_measures.py         # pytest: measure computation
│   └── test_translator.py       # pytest: PDDL translation
├── cli.py                       # Interactive CLI
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Container definition
└── pyproject.toml               # Project config & dependencies
```

## Test Scenarios

| Scenario                        | Category | Expected Profile | Description                           |
| ------------------------------- | -------- | ---------------- | ------------------------------------- |
| `edge_cases/coexisting_goals`   | Edge     | (0,0,0,0,0,0)    | Solvable, no conflicts                |
| `edge_cases/delete_relaxation`  | Edge     | (1,1,0,0,0,0)    | Delete effects block reachability     |
| `edge_cases/empty_goals`        | Edge     | (0,0,0,0,0,0)    | No goals defined                      |
| `edge_cases/single_goal`        | Edge     | (0,0,0,0,0,0)    | Trivial single goal                   |
| `mixed/rival_alliances`         | Mixed    | (0,0,2,1,2,2)    | Two sequencing conflicts              |
| `mixed/trust_travel`            | Mixed    | (0,0,2,1,2,1)    | Asymmetric sequencing conflict        |
| `p1_unreachability/bank_vault`  | P1       | (1,7,0,0,0,0)    | Chain with multiple unreachable props |
| `p1_unreachability/locked_door` | P1       | (1,3,0,0,0,0)    | Goal blocked by missing prerequisite  |
| `p2_mutex/light_switch`         | P2       | (0,0,2,1,0,0)    | Reversible toggle creates mutex       |
| `p2_mutex/traffic_light`        | P2       | (0,0,3,3,0,0)    | Three-way mutex clique                |

Profile format: `(ur_scope, ur_struct, mx_scope, mx_struct, gs_scope, gs_struct)`

## Architecture

The project separates into two independent layers:

- **Library** (`planning_measures/`): importable Python package with `compute_measures()`, `translate_pddl()`, and `batch_translate()`. No I/O, no terminal output, no dependencies beyond clingo.
- **CLI** (`cli.py`): interactive terminal interface that wraps the library. Menu-driven, colored output, CSV export. Not imported by the library or tests.

All measures are computed from a single brave reasoning pass over the ASP encoding:

- **`reachability.lp`** explores state traces up to `horizon` steps with full delete effects. Under `--enum-mode=brave`, clingo unions atoms across all answer sets.
- **`true_reachable/1`** derives actual reachability from `holds/2`, correctly handling delete effects (unlike the delete-relaxed fixpoint `reachable_prop/1`, which is retained only as a screening predicate).
- **`coexist_witness/2`** and **`g2_after_g1_witness/2`** provide mutex and sequencing data.
- **`measures.py`** computes P1 from set difference on `true_reachable`, P2/P3 from witness absence.

## Configuration

Default horizon is 20 steps. Override via:

```python
profile = compute_measures("problem.lp", horizon=100)
```
