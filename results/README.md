# Benchmark Results

_Part of [Planning Inconsistency Measures](../README.md)._

CSV outputs from running the measures on unsolvable-planning benchmarks. One row per PDDL problem. The CSV schema is in the root [README.md](../README.md#batch-benchmarking). Size, measure, and timing columns mirror the `ProblemSize`, `MeasureProfile`, and `TimingProfile` dataclasses. The run-specific `status` column values are documented below.

## Provenance

| Item     | Value             |
| -------- | ----------------- |
| Run date | 2026-04-02        |
| Horizon  | 20                |
| Timeout  | 120 s per problem |
| clingo   | 5.8.0             |
| plasp    | 3.1.1             |
| Python   | 3.12              |

## Benchmark sources

| File                                                                                                                        | Benchmark                         |
| --------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `3unsat.csv`                                                                                                                | Eriksson `3unsat`                 |
| `bottleneck.csv`, `cave-diving.csv`, `chessboard-pebbling.csv`, `diagnosis.csv`, `document-transfer.csv`, `pegsol-row5.csv` | `unsolve-ipc-2016/domains/FINAL/` |

See the root [README.md](../README.md) for the list of IPC 2016 domains that are incompatible with plasp or time out at the 120 s budget they are excluded from this set.

## `status` column

- `OK` - measures computed successfully.
- `TIMEOUT` - killed after 120 s (grounding or solving exceeded the budget).
- `ERROR: ...` - plasp rejected the instance. In `diagnosis.csv`, all `satprob*` rows error out because plasp cannot translate those variants; this is expected and does not affect the unsolvable (`prob*`) rows.

## Reproducing

```bash
./run.sh planning-measures batch \
  benchmarks/unsolve-ipc-2016/domains/FINAL/diagnosis/ \
  -o results/diagnosis.csv \
  -t 120
```

Swap the domain path to regenerate the other per-domain CSVs. See the thesis for discussion of these results.
