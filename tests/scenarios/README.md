# Test Scenarios

Hand-crafted ASP scenarios for verifying the planning inconsistency measures (P1-P3).

## Scenario Index

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

## Profile Format

`(I^scope_UR, I^struct_UR, I^scope_MX, I^struct_MX, I^scope_GS, I^struct_GS)`

| Component   | Measure           | Meaning                                                 |
| ----------- | ----------------- | ------------------------------------------------------- |
| I^scope_UR  | P1 Unreachability | Number of goals that are unreachable                    |
| I^struct_UR | P1 Unreachability | Number of propositions in unreachable dependency chains |
| I^scope_MX  | P2 Mutex          | Number of goals involved in mutex conflicts             |
| I^struct_MX | P2 Mutex          | Number of mutex pairs                                   |
| I^scope_GS  | P3 Sequencing     | Number of goals involved in sequencing conflicts        |
| I^struct_GS | P3 Sequencing     | Number of ordered pairs with sequencing conflicts       |

## Category Descriptions

### P1: Unreachability (`p1_unreachability/`)

Tests cases where goals cannot be reached from the initial state due to missing preconditions or impossible state transitions.

- **locked_door**: A goal requires a key that cannot be obtained
- **bank_vault**: Chain of dependencies where an early link is broken

### P2: Mutex (`p2_mutex/`)

Tests cases where goals are individually achievable but cannot coexist in any reachable state.

- **light_switch**: Two states (on/off) that are mutually exclusive
- **traffic_light**: Three-way mutual exclusion (red/yellow/green)

### P3: Mixed Conflicts (`mixed/`)

Tests cases with both mutex and sequencing conflicts, demonstrating that different conflict types can coexist.

- **trust_travel**: Achieving goal A makes goal B permanently unreachable
- **rival_alliances**: Multiple asymmetric sequencing dependencies

### Edge Cases (`edge_cases/`)

Tests boundary conditions and solvable instances to ensure no false positives.

- **coexisting_goals**: Multiple goals that can all be achieved together
- **single_goal**: Degenerate case with only one goal (no pairs to conflict)
- **empty_goals**: No goals defined (vacuously consistent)

## Directory Structure

```
tests/
├── test_measures.py           # pytest: measure computation
├── test_translator.py         # pytest: PDDL translation
├── pddl/                      # PDDL versions of scenarios
└── scenarios/
    ├── README.md              # This file
    ├── expected_profiles.txt  # Machine-readable expected values
    ├── p1_unreachability/     # Pure unreachability conflicts
    │   ├── locked_door.lp
    │   └── bank_vault.lp
    ├── p2_mutex/              # Pure mutex conflicts
    │   ├── light_switch.lp
    │   └── traffic_light.lp
    ├── mixed/                 # Multiple conflict types
    │   ├── trust_travel.lp
    │   └── rival_alliances.lp
    └── edge_cases/            # Zero-measure and trivial cases
        ├── coexisting_goals.lp
        ├── single_goal.lp
        └── empty_goals.lp
```

## Running Tests

```bash
# From repository root
./run.sh pytest tests/ -v

# Run only measure tests
./run.sh pytest tests/test_measures.py -v

# Run with pattern matching
./run.sh pytest tests/ -k "locked_door" -v
```

Expected output:

```
tests/test_measures.py::TestMeasures::test_scenario[p1_unreachability/locked_door] PASSED
tests/test_measures.py::TestMeasures::test_scenario[p1_unreachability/bank_vault] PASSED
...
9 passed
```

## Adding New Scenarios

1. **Create the scenario file** in the appropriate subdirectory:

   ```asp
   % tests/scenarios/p1_unreachability/my_scenario.lp

   % Initial state
   init(some_prop).

   % Goals
   goal(target_prop).

   % Operators
   operator(my_action).
   precond(my_action, some_prop).
   add(my_action, target_prop).
   ```

2. **Add expected profile** to `expected_profiles.txt`:

   ```
   p1_unreachability/my_scenario: (1, 2, 0, 0, 0, 0)
   ```

3. **Run verification**:
   ```bash
   ./run.sh pytest tests/test_measures.py -v
   ```

## Scenario File Format

Each `.lp` file defines a planning problem using these predicates:

| Predicate       | Description                                |
| --------------- | ------------------------------------------ |
| `init(P)`       | Proposition P is true in the initial state |
| `goal(P)`       | Proposition P is a goal                    |
| `operator(O)`   | O is an operator/action                    |
| `precond(O, P)` | Operator O requires proposition P          |
| `add(O, P)`     | Operator O makes proposition P true        |
| `delete(O, P)`  | Operator O makes proposition P false       |
