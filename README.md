# Thesis Planning Measures

ASP implementation of planning inconsistency measures (P1-P3) for Master's thesis.

## Measures

| Profile | Measure | Description                    |
| ------- | ------- | ------------------------------ |
| P1      | I_UR    | Unreachable goals/propositions |
| P2      | I_MX    | Goals in mutual exclusion      |
| P3      | I_GS    | Goals in sequencing conflict   |

## Setup

```bash
# Create environment with clingo
micromamba create -p ./.venv -c conda-forge clingo -y

# Install Python dependencies
.venv/bin/pip install -r requirements.txt
```

## Usage

Run measures on a scenario:

```bash
.venv/bin/clingo encodings/planning.lp encodings/reachability.lp \
                 encodings/measures/*.lp scenarios/locked_door.lp 1
```

Run all tests:

```bash
./tests/verify_measures.sh
```

Translate PDDL benchmarks:

```bash
# Single problem
.venv/bin/python tools/pddl_to_asp.py domain.pddl problem.pddl -o output.lp

# Batch translate
.venv/bin/python tools/batch_translate.py ~/benchmarks -o benchmarks/translated
```

Run experiments:

```bash
./tools/run_experiments.sh benchmarks/translated experiments/results.csv 60
```

## Structure

```
benchmarks/
  translated/          # Translated PDDL problems (generated)
encodings/
  measures/
    mutex.lp           # P2: mutex goal pairs
    sequencing.lp      # P3: sequencing conflicts
    unreachability.lp  # P1: unreachable goals
  planning.lp          # STRIPS problem representation
  reachability.lp      # Forward reachability analysis
experiments/           # Experiment results (CSV)
scenarios/             # Test planning problems (9 scenarios)
tests/
  pddl/                # PDDL versions of test scenarios
  verify_measures.sh   # Automated verification
tools/
  batch_translate.py   # Parallel batch translation
  pddl_to_asp.py       # PDDL to thesis ASP translator
  run_experiments.sh   # Benchmark runner (CSV output)
```

## Test Scenarios

| Scenario         | Tests            | Expected Profile |
| ---------------- | ---------------- | ---------------- |
| locked_door      | Unreachability   | (1,3,0,0,0,0)    |
| bank_vault       | Unreachability   | (1,7,0,0,0,0)    |
| light_switch     | Reversible mutex | (0,0,2,1,0,0)    |
| traffic_light    | Mutex clique     | (0,0,3,3,0,0)    |
| trust_travel     | Mixed conflicts  | (0,0,2,1,2,1)    |
| rival_alliances  | Mixed conflicts  | (0,0,2,1,2,2)    |
| coexisting_goals | No mutex         | (0,0,0,0,0,0)    |
| single_goal      | Single goal edge | (0,0,0,0,0,0)    |
| empty_goals      | No goals edge    | (0,0,0,0,0,0)    |

Profile format: `(I^scope_UR, I^struct_UR, I^scope_MX, I^struct_MX, I^scope_GS, I^struct_GS)`

## Limitations

- **Horizon**: State exploration uses `horizon=20` steps. Override via command line: `-c horizon=50`
- **Brave reasoning**: Mutex and sequencing measures require `--enum-mode=brave` to aggregate witnesses across all answer sets.
