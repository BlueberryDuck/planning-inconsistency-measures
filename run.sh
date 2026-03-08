#!/bin/bash
# Run commands in the Docker container.
#
# Usage:
#   ./run.sh                          # Shell inside container
#   ./run.sh pytest tests/ -v         # Run tests
#   ./run.sh planning-measures -h     # CLI help
#   ./run.sh planning-measures compute tests/scenarios/p1_unreachability/locked_door.lp

cd "$(dirname "$0")"

# If benchmarks/ is a symlink, mount its target so it resolves inside the container
EXTRA_ARGS=()
if [ -L benchmarks ]; then
    target=$(readlink -f benchmarks)
    EXTRA_ARGS+=(-v "$target:$target:ro")
fi

run() {
    docker compose run --rm "${EXTRA_ARGS[@]}" thesis "$@"
}

case "${1:-}" in
    planning-measures)
        shift
        run python -m planning_measures "$@"
    ;;
    "")
        run bash
    ;;
    *)
        run "$@"
    ;;
esac
