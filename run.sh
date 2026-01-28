#!/bin/bash
# Convenience wrapper for running commands in the Docker container
#
# Usage:
#   ./run.sh                           # Interactive shell
#   ./run.sh ./tests/run_all_tests.sh  # Run tests
#   ./run.sh clingo --version          # Run clingo

cd "$(dirname "$0")"
docker compose run --rm thesis "$@"
