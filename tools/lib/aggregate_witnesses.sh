#!/bin/bash
# ============================================================
# Shared P2/P3 Measure Computation via Brave Reasoning Witnesses
# ============================================================
#
# This library provides functions to compute mutex (P2) and sequencing (P3)
# measures from clingo brave reasoning output.
#
# Background:
#   Unlike P1 (unreachability), which can be computed deterministically,
#   P2 and P3 measures require examining ALL possible execution paths.
#   We use clingo's brave reasoning mode (--enum-mode=brave) to collect
#   witnesses across all answer sets, then aggregate them in bash.
#
# Witnesses:
#   - coexist_witness(G1, G2): Goals G1 and G2 coexist in some reachable state
#   - g2_after_g1_witness(G1, G2): G2 is reachable after achieving G1
#
# Measure Definitions:
#   - P2 Mutex: Goal pair (G1, G2) is in mutex if both are reachable but
#     no coexist_witness exists for them
#   - P3 Sequencing: Ordered pair (G1, G2) has a sequencing conflict if
#     both are reachable but no g2_after_g1_witness(G1, G2) exists
#
# Usage:
#   source tools/lib/aggregate_witnesses.sh
#   brave_output=$(clingo ... --enum-mode=brave 0 2>&1)
#   compute_p2_p3_measures "$brave_output"
#   echo "Mutex: scope=$mx_scope, struct=$mx_struct"
#   echo "Sequencing: scope=$gs_scope, struct=$gs_struct"
#
# ============================================================

# compute_p2_p3_measures
#
# Computes P2 (mutex) and P3 (sequencing) measures from brave reasoning output.
#
# Arguments:
#   $1 - Complete output from clingo run with --enum-mode=brave
#
# Sets global variables:
#   mx_scope  - Number of goals involved in at least one mutex conflict
#   mx_struct - Number of mutex pairs (unordered)
#   gs_scope  - Number of goals involved in at least one sequencing conflict
#   gs_struct - Number of sequencing conflict pairs (ordered)
#
# Note: This function uses bash associative arrays and requires bash 4.0+
compute_p2_p3_measures() {
    local brave_output="$1"

    # Extract goals and reachable propositions from brave output
    local goals=$(echo "$brave_output" | grep -oP 'goal\(\K[^)]+' | sort -u)
    local reachable=$(echo "$brave_output" | grep -oP 'reachable_prop\(\K[^)]+' | sort -u)

    # Collect brave witnesses (these appear across all answer sets)
    local coexist_witnesses=$(echo "$brave_output" | grep -oP 'coexist_witness\([^)]+\)' || true)
    local g2_after_witnesses=$(echo "$brave_output" | grep -oP 'g2_after_g1_witness\([^)]+\)' || true)

    # Convert goals to array for iteration
    local goal_arr
    readarray -t goal_arr <<< "$goals"

    # --------------------------------------------------------
    # Compute P2: Mutex pairs
    # --------------------------------------------------------
    # A pair (G1, G2) is in mutex if:
    #   1. Both G1 and G2 are reachable (achievable)
    #   2. No coexist_witness(G1, G2) or coexist_witness(G2, G1) exists
    #
    # mx_struct counts unordered pairs, mx_scope counts unique goals

    declare -A in_mutex
    mx_struct=0

    local i j g1 g2
    for ((i = 0; i < ${#goal_arr[@]}; i++)); do
        for ((j = i + 1; j < ${#goal_arr[@]}; j++)); do
            g1="${goal_arr[i]}"
            g2="${goal_arr[j]}"
            [[ -z "$g1" || -z "$g2" ]] && continue

            # Both must be achievable (reachable)
            echo "$reachable" | grep -qxF "$g1" || continue
            echo "$reachable" | grep -qxF "$g2" || continue

            # Mutex if no coexist witness exists (check both orderings)
            if ! echo "$coexist_witnesses" | grep -qE "coexist_witness\($g1,$g2\)|coexist_witness\($g2,$g1\)"; then
                mx_struct=$((mx_struct + 1))
                in_mutex["$g1"]=1
                in_mutex["$g2"]=1
            fi
        done
    done
    mx_scope=${#in_mutex[@]}

    # --------------------------------------------------------
    # Compute P3: Sequencing conflicts
    # --------------------------------------------------------
    # An ordered pair (G1, G2) has a sequencing conflict if:
    #   1. Both G1 and G2 are reachable
    #   2. No g2_after_g1_witness(G1, G2) exists
    #
    # This is asymmetric: (G1, G2) conflict doesn't imply (G2, G1) conflict
    # gs_struct counts ordered pairs, gs_scope counts unique goals

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

    # Clean up associative arrays to prevent leakage between calls
    unset in_mutex
    unset in_seq
}
