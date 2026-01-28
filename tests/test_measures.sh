#!/bin/bash
# Automated verification of planning inconsistency measures
#
# P1 (Unreachability): Computed deterministically in ASP
# P2 (Mutex) & P3 (Sequencing): Require brave reasoning aggregation
#   - Witnesses are collected across ALL answer sets
#   - Mutex: goals that NEVER coexist in any reachable state
#   - Sequencing: goal pairs where G2 is NEVER reachable after G1

cd "$(dirname "$0")/.."

# Source shared library
source tools/lib/aggregate_witnesses.sh

ENCODINGS="encodings/planning.lp encodings/reachability.lp"
MEASURES="encodings/measures/unreachability.lp encodings/measures/mutex.lp encodings/measures/sequencing.lp"

passed=0
failed=0

while IFS= read -r line; do
    [[ "$line" =~ ^# || -z "${line// /}" ]] && continue
    
    scenario="${line%%:*}"
    scenario="${scenario// /}"
    expected=$(echo "$line" | grep -oP '\(\K[^)]+' | tr -d ' ')
    
    printf "Testing %-20s " "$scenario..."
    
    # Run with all measures - unreachability is deterministic
    output=$(clingo $ENCODINGS $MEASURES "tests/scenarios/${scenario}.lp" 1 --warn=no-atom-undefined 2>&1)
    
    if ! echo "$output" | grep -q "SATISFIABLE"; then
        echo "ERROR: clingo failed"
        failed=$((failed + 1))
        continue
    fi
    
    # Extract P1 measures (deterministic)
    ur_scope=$(echo "$output" | grep -oP 'i_ur_scope\(\K[0-9]+' | head -1)
    ur_struct=$(echo "$output" | grep -oP 'i_ur_struct\(\K[0-9]+' | head -1)
    [[ -z "$ur_scope" ]] && ur_scope=0
    [[ -z "$ur_struct" ]] && ur_struct=0
    
    # For P2/P3, we need brave reasoning to aggregate witnesses
    brave=$(clingo $ENCODINGS "tests/scenarios/${scenario}.lp" --enum-mode=brave 0 --warn=no-atom-undefined 2>&1)
    
    # Compute P2/P3 measures using shared library
    compute_p2_p3_measures "$brave"
    
    actual="$ur_scope,$ur_struct,$mx_scope,$mx_struct,$gs_scope,$gs_struct"
    
    if [[ "$actual" == "$expected" ]]; then
        echo "PASS ($actual)"
        passed=$((passed + 1))
    else
        echo "FAIL"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        failed=$((failed + 1))
    fi
done < "tests/scenarios/expected_profiles.txt"

echo ""
echo "Results: $passed passed, $failed failed"
exit "$failed"
