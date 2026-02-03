#!/bin/bash
# Run commands in the Docker container
#
# Usage:
#   ./run.sh                    # Interactive shell
#   ./run.sh pytest tests/ -v   # Run tests
#   ./run.sh python cli.py      # Interactive CLI

cd "$(dirname "$0")"
docker compose run --rm thesis "$@"
