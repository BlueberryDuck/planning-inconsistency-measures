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
├── planning_measures/           # Library package
│   ├── __init__.py              # Public API
│   ├── measures.py              # Core computation
│   ├── profile.py               # MeasureProfile dataclass
│   ├── solver.py                # Clingo wrapper
│   ├── translator.py            # PDDL to ASP translator
│   └── batch_translator.py      # Batch PDDL translator
├── encodings/
│   ├── planning.lp              # STRIPS problem representation
│   ├── reachability.lp          # Forward reachability + witnesses
│   └── measures.lp              # P1 computation (deterministic)
├── tests/
│   ├── test_measures.py         # pytest: measure computation
│   ├── test_translator.py       # pytest: PDDL translation
│   ├── scenarios/               # ASP test scenarios
│   └── pddl/                    # PDDL test cases
├── cli.py                       # Interactive CLI
├── pyproject.toml               # Project config & dependencies
├── Dockerfile                   # Container definition
└── docker-compose.yml           # Container orchestration
```

## Test Scenarios

| Scenario                        | Category | Expected Profile | Description                           |
| ------------------------------- | -------- | ---------------- | ------------------------------------- |
| `p1_unreachability/locked_door` | P1       | (1,3,0,0,0,0)    | Goal blocked by missing prerequisite  |
| `p1_unreachability/bank_vault`  | P1       | (1,7,0,0,0,0)    | Chain with multiple unreachable props |
| `p2_mutex/light_switch`         | P2       | (0,0,2,1,0,0)    | Reversible toggle creates mutex       |
| `p2_mutex/traffic_light`        | P2       | (0,0,3,3,0,0)    | Three-way mutex clique                |
| `mixed/trust_travel`            | Mixed    | (0,0,2,1,2,1)    | Asymmetric sequencing conflict        |
| `mixed/rival_alliances`         | Mixed    | (0,0,2,1,2,2)    | Two sequencing conflicts              |
| `edge_cases/coexisting_goals`   | Edge     | (0,0,0,0,0,0)    | Solvable - no conflicts               |
| `edge_cases/single_goal`        | Edge     | (0,0,0,0,0,0)    | Trivial single goal                   |
| `edge_cases/empty_goals`        | Edge     | (0,0,0,0,0,0)    | No goals defined                      |

Profile format: `(ur_scope, ur_struct, mx_scope, mx_struct, gs_scope, gs_struct)`

## Architecture

- **ASP Encodings** (`encodings/`): Compute reachability and generate witnesses
- **Python Library** (`planning_measures/`): Aggregate witnesses into measures
- **Interactive CLI** (`cli.py`): Menu-driven terminal interface

P1 is computed deterministically in ASP. P2 and P3 use brave reasoning to collect
witnesses across all answer sets, then Python computes set differences.

## Configuration

Default horizon is 20 steps. Override via:

```python
profile = compute_measures("problem.lp", horizon=100)
```
