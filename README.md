# Thesis Planning Measures

ASP implementation of planning inconsistency measures (P1-P3) for Master's thesis.

## Overview

This project implements three measures to quantify different types of goal conflicts in classical planning problems:

| Measure | Name                  | Description                                                         |
| ------- | --------------------- | ------------------------------------------------------------------- |
| P1      | I_UR (Unreachability) | Goals or propositions that cannot be reached from the initial state |
| P2      | I_MX (Mutex)          | Achievable goals that can never coexist in any reachable state      |
| P3      | I_GS (Sequencing)     | Goal pairs where achieving one prevents achieving another           |

Each measure has two variants:

- **scope**: Number of goals involved in conflicts
- **struct**: Number of conflicting pairs/propositions

## Setup

Requires Docker.

```bash
docker compose build
```

## Quick Start

```bash
# Run measures on a scenario
./run.sh clingo encodings/planning.lp encodings/reachability.lp \
         encodings/measures/*.lp tests/scenarios/p1_unreachability/locked_door.lp 1

# Run all tests (26 tests)
./run.sh ./tests/run_all_tests.sh

# Run specific test suite
./run.sh ./tests/run_all_tests.sh measures      # ASP scenario tests
./run.sh ./tests/run_all_tests.sh translator    # PDDL translator tests
./run.sh ./tests/run_all_tests.sh batch         # Batch translator tests
./run.sh ./tests/run_all_tests.sh experiments   # Experiment runner tests

# Translate a PDDL problem
./run.sh python tools/pddl_to_asp.py domain.pddl problem.pddl -o output.lp

# Batch translate benchmarks
./run.sh python tools/batch_translate.py ~/benchmarks/ipc2016 \
         -o benchmarks/translated/ipc2016 -j 4

# Run experiments with 60s timeout
./run.sh ./tools/run_experiments.sh benchmarks/translated experiments/results.csv 60

# Interactive shell
./run.sh
```

## Project Structure

```
thesis-planning-measures/
├── config/
│   └── defaults.lp              # Default constants (horizon=20)
├── encodings/
│   ├── planning.lp              # STRIPS problem representation
│   ├── reachability.lp          # Forward reachability analysis
│   └── measures/
│       ├── unreachability.lp    # P1: unreachable goals
│       ├── mutex.lp             # P2: mutex goal pairs
│       └── sequencing.lp        # P3: sequencing conflicts
├── tests/
│   ├── run_all_tests.sh         # Master test runner
│   ├── test_measures.sh         # ASP scenario verification
│   ├── test_translator.sh       # PDDL translator tests
│   ├── test_batch_translate.sh  # Batch translator tests
│   ├── test_experiment_runner.sh # Experiment runner tests
│   ├── pddl/                    # PDDL test cases
│   │   ├── locked_door/         # P1 test case
│   │   └── trust_travel/        # Mixed test case
│   └── scenarios/               # ASP test scenarios
│       ├── expected_profiles.txt
│       ├── p1_unreachability/
│       ├── p2_mutex/
│       ├── mixed/
│       └── edge_cases/
├── tools/
│   ├── lib/
│   │   └── aggregate_witnesses.sh   # Shared P2/P3 computation
│   ├── pddl_to_asp.py           # PDDL -> thesis ASP translator
│   ├── batch_translate.py       # Parallel batch translation
│   ├── run_experiments.sh       # Benchmark runner (CSV output)
│   ├── horizon_analysis.sh      # Horizon sensitivity testing
│   └── verify_solvable.sh       # Phase 1 sanity check
├── benchmarks/
│   └── translated/              # Translated PDDL problems (generated)
├── experiments/                 # Experiment results (CSV, markdown)
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Container orchestration
└── run.sh                       # Convenience wrapper
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

Profile format: `(I^scope_UR, I^struct_UR, I^scope_MX, I^struct_MX, I^scope_GS, I^struct_GS)`

## Tools

### pddl_to_asp.py

Translates PDDL domain/problem pairs to the thesis ASP format.

```bash
./run.sh python tools/pddl_to_asp.py domain.pddl problem.pddl -o output.lp
```

### batch_translate.py

Parallel batch translation of PDDL benchmarks. Handles common IPC directory structures.

```bash
./run.sh python tools/batch_translate.py ~/benchmarks/ipc2016 \
         -o benchmarks/translated -j 4 --verbose

# Preview without translating
./run.sh python tools/batch_translate.py ~/benchmarks/ipc2016 --dry-run
```

### run_experiments.sh

Runs measures on all translated problems, producing CSV output with:

- Domain and problem names
- All six measure values (scope and struct for P1-P3)
- Category classification (2a, 2c-mutex, 2c-sequencing, undetected)
- Runtime and status

```bash
./tools/run_experiments.sh benchmarks/translated experiments/results.csv 60
```

### horizon_analysis.sh

Tests horizon sensitivity on solvable instances to determine appropriate horizon values.

```bash
./tools/horizon_analysis.sh benchmarks/translated experiments/horizon_analysis.csv
```

### verify_solvable.sh

Phase 1 verification: ensures all solvable instances (`*satprob*.lp`) have zero measures.

```bash
./tools/verify_solvable.sh benchmarks/translated/ipc2016
# Outputs: experiments/phase1_verification.md
```

## Configuration

Default constants are defined in `config/defaults.lp`:

```asp
#const horizon = 20.
```

Override via command line:

```bash
./run.sh clingo ... -c horizon=100
```

## Technical Notes

### Measure Computation

- **P1 (Unreachability)**: Computed deterministically in a single answer set using forward reachability fixpoint.
- **P2 (Mutex) & P3 (Sequencing)**: Require brave reasoning (`--enum-mode=brave`) to aggregate witnesses across all answer sets. The shell scripts handle this automatically.

### Horizon Parameter

The `horizon` constant limits state-space exploration depth. If measures report false positives on known-solvable instances, increase the horizon. The `horizon_analysis.sh` script helps determine appropriate values.

### Category Classification

The experiment runner classifies problems into categories based on detected conflicts:

- **2a**: Unreachability detected (I_UR > 0)
- **2c-sequencing**: Sequencing conflicts detected (I_GS > 0, I_UR = 0)
- **2c-mutex**: Only mutex conflicts detected (I_MX > 0, I_UR = I_GS = 0)
- **undetected**: No conflicts found (all measures zero)
