#!/bin/bash
# Automated verification of planning inconsistency measures
#
# P1 (Unreachability): Computed deterministically in ASP
# P2 (Mutex) & P3 (Sequencing): Require brave reasoning aggregation
#   - Witnesses are collected across ALL answer sets
#   - Mutex: goals that NEVER coexist in any reachable state
#   - Sequencing: goal pairs where G2 is NEVER reachable after G1

cd "$(dirname "$0")/.."

CLINGO=".venv/bin/clingo"
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
    output=$($CLINGO $ENCODINGS $MEASURES "scenarios/${scenario}.lp" 1 2>&1)

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
    brave=$($CLINGO $ENCODINGS "scenarios/${scenario}.lp" --enum-mode=brave 0 2>&1)

    # Get goals and reachable props from clingo output
    goals=$(echo "$brave" | grep -oP 'goal\(\K[^)]+' | sort -u)
    reachable=$(echo "$brave" | grep -oP 'reachable_prop\(\K[^)]+' | sort -u)

    # Collect brave witnesses
    coexist_witnesses=$(echo "$brave" | grep -oP 'coexist_witness\([^)]+\)' || true)
    g2_after_witnesses=$(echo "$brave" | grep -oP 'g2_after_g1_witness\([^)]+\)' || true)

    # Convert goals to array
    readarray -t goal_arr <<< "$goals"

    # Compute P2: Mutex pairs (achievable goals that never coexist)
    declare -A in_mutex
    mx_struct=0

    for ((i = 0; i < ${#goal_arr[@]}; i++)); do
        for ((j = i + 1; j < ${#goal_arr[@]}; j++)); do
            g1="${goal_arr[i]}"
            g2="${goal_arr[j]}"
            [[ -z "$g1" || -z "$g2" ]] && continue

            # Both must be achievable (reachable)
            echo "$reachable" | grep -qxF "$g1" || continue
            echo "$reachable" | grep -qxF "$g2" || continue

            # Mutex if no coexist witness exists (either ordering)
            if ! echo "$coexist_witnesses" | grep -qE "coexist_witness\($g1,$g2\)|coexist_witness\($g2,$g1\)"; then
                mx_struct=$((mx_struct + 1))
                in_mutex["$g1"]=1
                in_mutex["$g2"]=1
            fi
        done
    done
    mx_scope=${#in_mutex[@]}

    # Compute P3: Sequencing conflicts (ordered pairs where G2 unreachable after G1)
    declare -A in_seq
    gs_struct=0

    for g1 in "${goal_arr[@]}"; do
        for g2 in "${goal_arr[@]}"; do
            [[ "$g1" == "$g2" || -z "$g1" || -z "$g2" ]] && continue

            echo "$reachable" | grep -qxF "$g1" || continue
            echo "$reachable" | grep -qxF "$g2" || continue

            # Conflict if no witness that G2 is reachable after G1
            if ! echo "$g2_after_witnesses" | grep -q "g2_after_g1_witness($g1,$g2)"; then
                gs_struct=$((gs_struct + 1))
                in_seq["$g1"]=1
                in_seq["$g2"]=1
            fi
        done
    done
    gs_scope=${#in_seq[@]}

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

    unset in_mutex
    unset in_seq
done < "expected_profiles.txt"

echo ""
echo "Results: $passed passed, $failed failed"
exit "$failed"
