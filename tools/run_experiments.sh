#!/bin/bash
# Run inconsistency measure experiments on translated PDDL benchmarks
#
# Produces CSV output with measure profiles for each problem.
# Uses brave reasoning for P2/P3 aggregation (same method as verify_measures.sh).
#
# Usage:
#   ./tools/run_experiments.sh [input_dir] [output_csv] [timeout_sec]
#
# Example:
#   ./tools/run_experiments.sh benchmarks/translated results.csv 60

cd "$(dirname "$0")/.."

INPUT_DIR="${1:-benchmarks/translated}"
OUTPUT_CSV="${2:-experiments/results.csv}"
TIMEOUT="${3:-60}"

CLINGO=".venv/bin/clingo"
ENCODINGS="encodings/planning.lp encodings/reachability.lp"
MEASURES="encodings/measures/unreachability.lp encodings/measures/mutex.lp encodings/measures/sequencing.lp"

# Create output directory
mkdir -p "$(dirname "$OUTPUT_CSV")"

# Write CSV header
echo "problem,i_ur_scope,i_ur_struct,i_mx_scope,i_mx_struct,i_gs_scope,i_gs_struct,time_s,status" > "$OUTPUT_CSV"

# Count problems
total=$(find "$INPUT_DIR" -name "*.lp" -type f 2>/dev/null | wc -l)
if [[ "$total" -eq 0 ]]; then
    echo "No .lp files found in $INPUT_DIR"
    exit 1
fi

echo "Running experiments on $total problem(s) from $INPUT_DIR"
echo "Timeout: ${TIMEOUT}s per problem"
echo "Output: $OUTPUT_CSV"
echo ""

current=0

for problem_file in "$INPUT_DIR"/*.lp; do
    current=$((current + 1))
    problem_name=$(basename "$problem_file" .lp)

    printf "[%3d/%3d] %-40s " "$current" "$total" "$problem_name"

    start_time=$(date +%s.%N)

    # Run clingo for P1 (deterministic) with timeout
    # Note: clingo exit codes: 10=SAT, 20=UNSAT, 30=finished enumeration
    output=$(timeout "${TIMEOUT}s" $CLINGO $ENCODINGS $MEASURES "$problem_file" 1 2>&1)
    exit_code=$?

    if [[ $exit_code -eq 124 ]]; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        echo "TIMEOUT"
        echo "$problem_name,,,,,,,${elapsed},TIMEOUT" >> "$OUTPUT_CSV"
        continue
    fi

    if [[ $exit_code -ne 10 && $exit_code -ne 30 ]]; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        echo "ERROR (exit $exit_code)"
        echo "$problem_name,,,,,,,${elapsed},ERROR" >> "$OUTPUT_CSV"
        continue
    fi

    # Check if satisfiable
    if ! echo "$output" | grep -q "SATISFIABLE"; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        echo "UNSAT"
        echo "$problem_name,,,,,,,${elapsed},UNSAT" >> "$OUTPUT_CSV"
        continue
    fi

    # Extract P1 measures (deterministic)
    ur_scope=$(echo "$output" | grep -oP 'i_ur_scope\(\K[0-9]+' | head -1)
    ur_struct=$(echo "$output" | grep -oP 'i_ur_struct\(\K[0-9]+' | head -1)
    [[ -z "$ur_scope" ]] && ur_scope=0
    [[ -z "$ur_struct" ]] && ur_struct=0

    # Calculate remaining time for brave reasoning
    current_time=$(date +%s.%N)
    elapsed_so_far=$(awk "BEGIN {printf \"%.0f\", $current_time - $start_time}")
    remaining=$((TIMEOUT - elapsed_so_far))

    if [[ $remaining -le 0 ]]; then
        elapsed=$(awk "BEGIN {printf \"%.3f\", $current_time - $start_time}")
        echo "TIMEOUT (no time for brave)"
        echo "$problem_name,$ur_scope,$ur_struct,,,,${elapsed},TIMEOUT_BRAVE" >> "$OUTPUT_CSV"
        continue
    fi

    # Run brave reasoning for P2/P3 witness aggregation
    brave=$(timeout "${remaining}s" $CLINGO $ENCODINGS "$problem_file" --enum-mode=brave 0 2>&1)
    brave_exit=$?

    if [[ $brave_exit -eq 124 ]]; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        echo "TIMEOUT (brave)"
        echo "$problem_name,$ur_scope,$ur_struct,,,,${elapsed},TIMEOUT_BRAVE" >> "$OUTPUT_CSV"
        continue
    fi

    if [[ $brave_exit -ne 10 && $brave_exit -ne 30 ]]; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        echo "ERROR (brave exit $brave_exit)"
        echo "$problem_name,$ur_scope,$ur_struct,,,,${elapsed},ERROR_BRAVE" >> "$OUTPUT_CSV"
        continue
    fi

    # Get goals and reachable props
    goals=$(echo "$brave" | grep -oP 'goal\(\K[^)]+' | sort -u)
    reachable=$(echo "$brave" | grep -oP 'reachable_prop\(\K[^)]+' | sort -u)

    # Collect brave witnesses
    coexist_witnesses=$(echo "$brave" | grep -oP 'coexist_witness\([^)]+\)' || true)
    g2_after_witnesses=$(echo "$brave" | grep -oP 'g2_after_g1_witness\([^)]+\)' || true)

    # Convert goals to array
    readarray -t goal_arr <<< "$goals"

    # Compute P2: Mutex pairs
    declare -A in_mutex
    mx_struct=0

    for ((i = 0; i < ${#goal_arr[@]}; i++)); do
        for ((j = i + 1; j < ${#goal_arr[@]}; j++)); do
            g1="${goal_arr[i]}"
            g2="${goal_arr[j]}"
            [[ -z "$g1" || -z "$g2" ]] && continue

            # Both must be reachable
            echo "$reachable" | grep -qxF "$g1" || continue
            echo "$reachable" | grep -qxF "$g2" || continue

            # Mutex if no coexist witness
            if ! echo "$coexist_witnesses" | grep -qE "coexist_witness\($g1,$g2\)|coexist_witness\($g2,$g1\)"; then
                mx_struct=$((mx_struct + 1))
                in_mutex["$g1"]=1
                in_mutex["$g2"]=1
            fi
        done
    done
    mx_scope=${#in_mutex[@]}

    # Compute P3: Sequencing conflicts
    declare -A in_seq
    gs_struct=0

    for g1 in "${goal_arr[@]}"; do
        for g2 in "${goal_arr[@]}"; do
            [[ "$g1" == "$g2" || -z "$g1" || -z "$g2" ]] && continue

            echo "$reachable" | grep -qxF "$g1" || continue
            echo "$reachable" | grep -qxF "$g2" || continue

            # Conflict if no g2_after_g1 witness
            if ! echo "$g2_after_witnesses" | grep -q "g2_after_g1_witness($g1,$g2)"; then
                gs_struct=$((gs_struct + 1))
                in_seq["$g1"]=1
                in_seq["$g2"]=1
            fi
        done
    done
    gs_scope=${#in_seq[@]}

    end_time=$(date +%s.%N)
    elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")

    echo "($ur_scope,$ur_struct,$mx_scope,$mx_struct,$gs_scope,$gs_struct) ${elapsed}s"
    echo "$problem_name,$ur_scope,$ur_struct,$mx_scope,$mx_struct,$gs_scope,$gs_struct,$elapsed,OK" >> "$OUTPUT_CSV"

    unset in_mutex
    unset in_seq
done

echo ""
echo "Results written to $OUTPUT_CSV"

# Summary statistics
total_ok=$(grep -c ",OK$" "$OUTPUT_CSV" || true)
total_timeout=$(grep -c "TIMEOUT" "$OUTPUT_CSV" || true)
total_error=$(grep -c "ERROR" "$OUTPUT_CSV" || true)

echo "Summary: $total_ok OK, $total_timeout timeout, $total_error error"
