# Thesis Planning Measures

ASP implementation of planning inconsistency measures for Master's thesis.

## Setup

```bash
# Install micromamba (if needed)
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C /tmp bin/micromamba

# Create environment with clingo
/tmp/bin/micromamba create -p ./.venv -c conda-forge clingo -y
```

## Dependencies

- clingo 5.8.0+ (installed in `.venv/`)

## Structure

- `encodings/` - ASP measure implementations
- `scenarios/` - Test planning problems
- `tests/` - Verification scripts

## Usage

Run measures on a scenario:
```bash
.venv/bin/clingo encodings/planning.lp encodings/reachability.lp \
                 encodings/measures/*.lp scenarios/locked_door.lp 0
```

Run all tests:
```bash
./tests/verify_measures.sh
```
