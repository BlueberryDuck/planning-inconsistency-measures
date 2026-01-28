#!/bin/bash
# Phase 1 Verification: Solvable Instance Sanity Check
#
# Verifies that all solvable instances (satprob*.lp) have zero measures.
# This validates that the measures correctly identify solvable problems.
#
# Usage:
#   ./tools/verify_solvable.sh [input_dir]
#
# Example:
#   ./tools/verify_solvable.sh benchmarks/translated/ipc2016

cd "$(dirname "$0")/.."

# Source shared library
source tools/lib/aggregate_witnesses.sh

INPUT_DIR="${1:-benchmarks/translated}"
OUTPUT_MD="experiments/phase1_verification.md"

ENCODINGS="encodings/planning.lp encodings/reachability.lp"
MEASURES="encodings/measures/unreachability.lp encodings/measures/mutex.lp encodings/measures/sequencing.lp"

# Timeout per run (seconds)
TIMEOUT=120

# Create output directory
mkdir -p "$(dirname "$OUTPUT_MD")"

# Find solvable instances
solvable_files=$(find "$INPUT_DIR" -name "*satprob*.lp" -type f 2>/dev/null | sort)

if [[ -z "$solvable_files" ]]; then
    echo "No solvable instances (*satprob*.lp) found in $INPUT_DIR"
    exit 1
fi

total=$(echo "$solvable_files" | wc -l)

echo "Phase 1 Verification: Solvable Instance Sanity Check"
echo "====================================================="
echo ""
echo "Input: $INPUT_DIR"
echo "Found: $total solvable instance(s)"
echo ""

# Initialize counters
passed=0
failed=0
errors=0
declare -a failed_problems

current=0

for problem_file in $solvable_files; do
    current=$((current + 1))
    problem_name=$(basename "$problem_file" .lp)

    printf "[%3d/%3d] %-50s " "$current" "$total" "$problem_name"

    # Run clingo for all measures
    output=$(timeout "${TIMEOUT}s" clingo $ENCODINGS $MEASURES "$problem_file" 1 --warn=no-atom-undefined 2>&1)
    exit_code=$?

    if [[ $exit_code -eq 124 ]]; then
        echo "TIMEOUT"
        errors=$((errors + 1))
        failed_problems+=("$problem_name: TIMEOUT")
        continue
    fi

    if [[ $exit_code -ne 10 && $exit_code -ne 30 ]]; then
        echo "ERROR (exit $exit_code)"
        errors=$((errors + 1))
        failed_problems+=("$problem_name: ERROR (exit $exit_code)")
        continue
    fi

    if ! echo "$output" | grep -q "SATISFIABLE"; then
        echo "UNSAT"
        errors=$((errors + 1))
        failed_problems+=("$problem_name: UNSAT")
        continue
    fi

    # Extract P1 measures
    ur_scope=$(echo "$output" | grep -oP 'i_ur_scope\(\K[0-9]+' | head -1)
    ur_struct=$(echo "$output" | grep -oP 'i_ur_struct\(\K[0-9]+' | head -1)
    [[ -z "$ur_scope" ]] && ur_scope=0
    [[ -z "$ur_struct" ]] && ur_struct=0

    # Run brave reasoning for P2/P3
    brave=$(timeout "${TIMEOUT}s" clingo $ENCODINGS "$problem_file" --enum-mode=brave 0 --warn=no-atom-undefined 2>&1)
    brave_exit=$?

    if [[ $brave_exit -eq 124 ]]; then
        echo "TIMEOUT (brave)"
        errors=$((errors + 1))
        failed_problems+=("$problem_name: TIMEOUT (brave)")
        continue
    fi

    if [[ $brave_exit -ne 10 && $brave_exit -ne 30 ]]; then
        echo "ERROR (brave exit $brave_exit)"
        errors=$((errors + 1))
        failed_problems+=("$problem_name: ERROR (brave)")
        continue
    fi

    # Compute P2/P3 measures
    compute_p2_p3_measures "$brave"

    # Check if all measures are zero
    if [[ "$ur_scope" -eq 0 && "$ur_struct" -eq 0 && \
          "$mx_scope" -eq 0 && "$mx_struct" -eq 0 && \
          "$gs_scope" -eq 0 && "$gs_struct" -eq 0 ]]; then
        echo "PASS (0,0,0,0,0,0)"
        passed=$((passed + 1))
    else
        echo "FAIL ($ur_scope,$ur_struct,$mx_scope,$mx_struct,$gs_scope,$gs_struct)"
        failed=$((failed + 1))
        failed_problems+=("$problem_name: ($ur_scope,$ur_struct,$mx_scope,$mx_struct,$gs_scope,$gs_struct)")
    fi
done

echo ""
echo "====================================================="
echo "Results: $passed PASS, $failed FAIL, $errors ERROR"

# Calculate pass rate
total_run=$((passed + failed))
if [[ $total_run -gt 0 ]]; then
    pass_rate=$(awk "BEGIN {printf \"%.1f\", 100 * $passed / $total_run}")
    echo "Pass rate: ${pass_rate}% ($passed/$total_run)"
else
    pass_rate="N/A"
fi

# Write markdown report
{
    echo "# Phase 1 Verification Report"
    echo ""
    echo "**Date**: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Input**: \`$INPUT_DIR\`"
    echo ""
    echo "## Summary"
    echo ""
    echo "| Metric | Value |"
    echo "|--------|-------|"
    echo "| Total solvable instances | $total |"
    echo "| Passed (all zeros) | $passed |"
    echo "| Failed (non-zero) | $failed |"
    echo "| Errors (timeout/unsat) | $errors |"
    echo "| **Pass rate** | **${pass_rate}%** |"
    echo ""

    if [[ ${#failed_problems[@]} -gt 0 ]]; then
        echo "## Failed/Error Problems"
        echo ""
        for prob in "${failed_problems[@]}"; do
            echo "- $prob"
        done
        echo ""
    fi

    echo "## Interpretation"
    echo ""
    if [[ $failed -eq 0 && $errors -eq 0 ]]; then
        echo "All solvable instances have zero measures, as expected. The measures correctly identify these as conflict-free."
    elif [[ $failed -gt 0 ]]; then
        echo "Some solvable instances have non-zero measures. This may indicate:"
        echo "- Insufficient horizon (try increasing with \`-c horizon=100\`)"
        echo "- Issues with the encoding or translation"
        echo "- False positives in the measure detection"
    fi
} > "$OUTPUT_MD"

echo ""
echo "Report written to: $OUTPUT_MD"

# Exit with failure if any tests failed
[[ $failed -eq 0 && $errors -eq 0 ]] && exit 0 || exit 1
