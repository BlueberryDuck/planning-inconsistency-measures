#!/bin/bash
# Horizon Sensitivity Analysis
#
# Tests solvable IPC instances at different horizons (20, 50, 100, 200)
# to determine the minimum horizon at which all measures become zero.
#
# Usage:
#   ./tools/horizon_analysis.sh [input_dir] [output_csv]
#
# Example:
#   ./tools/horizon_analysis.sh benchmarks/translated experiments/horizon_analysis.csv

cd "$(dirname "$0")/.."

INPUT_DIR="${1:-benchmarks/translated}"
OUTPUT_CSV="${2:-experiments/horizon_analysis.csv}"

CLINGO=".venv/bin/clingo"
ENCODINGS="encodings/planning.lp encodings/reachability.lp"
MEASURES="encodings/measures/unreachability.lp encodings/measures/mutex.lp encodings/measures/sequencing.lp"

# Horizons to test
HORIZONS=(20 50 100 200)

# Timeout per run (seconds)
TIMEOUT=120

# Create output directory
mkdir -p "$(dirname "$OUTPUT_CSV")"

# Write CSV header
echo "problem,horizon,i_ur_scope,i_ur_struct,time_s,status" > "$OUTPUT_CSV"

# Find solvable instances (satprob*.lp files)
solvable_files=$(find "$INPUT_DIR" -name "*satprob*.lp" -type f 2>/dev/null | sort | head -10)

if [[ -z "$solvable_files" ]]; then
    echo "No solvable instances (*satprob*.lp) found in $INPUT_DIR"
    echo "Falling back to first 5 .lp files..."
    solvable_files=$(find "$INPUT_DIR" -name "*.lp" -type f 2>/dev/null | sort | head -5)
fi

if [[ -z "$solvable_files" ]]; then
    echo "No .lp files found in $INPUT_DIR"
    exit 1
fi

total=$(echo "$solvable_files" | wc -l)
echo "Running horizon analysis on $total instance(s)"
echo "Horizons: ${HORIZONS[*]}"
echo "Output: $OUTPUT_CSV"
echo ""

current=0

for problem_file in $solvable_files; do
    current=$((current + 1))
    problem_name=$(basename "$problem_file" .lp)

    echo "[$current/$total] $problem_name"

    for horizon in "${HORIZONS[@]}"; do
        printf "  horizon=%3d: " "$horizon"

        start_time=$(date +%s.%N)

        # Run with specific horizon (override default)
        output=$(timeout "${TIMEOUT}s" $CLINGO $ENCODINGS $MEASURES "$problem_file" 1 \
                 -c horizon="$horizon" --warn=no-atom-undefined 2>&1)
        exit_code=$?

        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")

        if [[ $exit_code -eq 124 ]]; then
            echo "TIMEOUT"
            echo "$problem_name,$horizon,,,${elapsed},TIMEOUT" >> "$OUTPUT_CSV"
            continue
        fi

        if [[ $exit_code -ne 10 && $exit_code -ne 30 ]]; then
            echo "ERROR (exit $exit_code)"
            echo "$problem_name,$horizon,,,${elapsed},ERROR" >> "$OUTPUT_CSV"
            continue
        fi

        if ! echo "$output" | grep -q "SATISFIABLE"; then
            echo "UNSAT"
            echo "$problem_name,$horizon,,,${elapsed},UNSAT" >> "$OUTPUT_CSV"
            continue
        fi

        # Extract P1 measures (focus on unreachability for horizon analysis)
        ur_scope=$(echo "$output" | grep -oP 'i_ur_scope\(\K[0-9]+' | head -1)
        ur_struct=$(echo "$output" | grep -oP 'i_ur_struct\(\K[0-9]+' | head -1)
        [[ -z "$ur_scope" ]] && ur_scope=0
        [[ -z "$ur_struct" ]] && ur_struct=0

        if [[ "$ur_scope" -eq 0 && "$ur_struct" -eq 0 ]]; then
            echo "OK (0,0) ${elapsed}s"
        else
            echo "($ur_scope,$ur_struct) ${elapsed}s"
        fi

        echo "$problem_name,$horizon,$ur_scope,$ur_struct,$elapsed,OK" >> "$OUTPUT_CSV"
    done
    echo ""
done

echo "Results written to $OUTPUT_CSV"
echo ""

# Analyze results: find minimum horizon where all measures are zero
echo "=== Analysis Summary ==="
echo ""
echo "First zero-measure horizon by problem:"

for problem_file in $solvable_files; do
    problem_name=$(basename "$problem_file" .lp)
    first_zero=$(grep "^$problem_name," "$OUTPUT_CSV" | \
                 awk -F, '$3==0 && $4==0 && $6=="OK" {print $2; exit}')
    if [[ -n "$first_zero" ]]; then
        echo "  $problem_name: horizon=$first_zero"
    else
        echo "  $problem_name: not zero at any tested horizon"
    fi
done

echo ""
echo "Recommendation: Set default horizon to max(first_zero) * 1.5"
