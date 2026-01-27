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

# Source shared library
source tools/lib/aggregate_witnesses.sh

INPUT_DIR="${1:-benchmarks/translated}"
OUTPUT_CSV="${2:-experiments/results.csv}"
TIMEOUT="${3:-60}"

CLINGO=".venv/bin/clingo"
ENCODINGS="encodings/planning.lp encodings/reachability.lp"
MEASURES="encodings/measures/unreachability.lp encodings/measures/mutex.lp encodings/measures/sequencing.lp"

# Helper function to extract domain name from translated problem
extract_domain() {
    grep -m1 "^% Domain:" "$1" 2>/dev/null | sed 's/^% Domain: *//' | tr -d '[:space:]'
}

# Classify problem category based on measure profile
classify_category() {
    local ur="$1" mx="$2" gs="$3"
    if [[ "$ur" -gt 0 ]]; then echo "2a"
    elif [[ "$gs" -gt 0 ]]; then echo "2c-sequencing"
    elif [[ "$mx" -gt 0 ]]; then echo "2c-mutex"
    else echo "undetected"; fi
}

# Create output directory
mkdir -p "$(dirname "$OUTPUT_CSV")"

# Write CSV header (11 fields)
echo "domain,problem,i_ur_scope,i_ur_struct,i_mx_scope,i_mx_struct,i_gs_scope,i_gs_struct,category,time_s,status" > "$OUTPUT_CSV"

# Find all .lp files recursively
mapfile -t problem_files < <(find "$INPUT_DIR" -name "*.lp" -type f 2>/dev/null | sort)
total=${#problem_files[@]}

if [[ "$total" -eq 0 ]]; then
    echo "No .lp files found in $INPUT_DIR"
    exit 1
fi

echo "Running experiments on $total problem(s) from $INPUT_DIR"
echo "Timeout: ${TIMEOUT}s per problem"
echo "Output: $OUTPUT_CSV"
echo ""

current=0

for problem_file in "${problem_files[@]}"; do
    current=$((current + 1))
    problem_name=$(basename "$problem_file" .lp)
    domain_name=$(extract_domain "$problem_file")
    [[ -z "$domain_name" ]] && domain_name="unknown"

    printf "[%3d/%3d] %-40s " "$current" "$total" "$problem_name"

    start_time=$(date +%s.%N)

    # Run clingo for P1 (deterministic) with timeout
    # Note: clingo exit codes: 10=SAT, 20=UNSAT, 30=finished enumeration
    output=$(timeout "${TIMEOUT}s" $CLINGO $ENCODINGS $MEASURES "$problem_file" 1 --warn=no-atom-undefined 2>&1)
    exit_code=$?

    if [[ $exit_code -eq 124 ]]; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        echo "TIMEOUT"
        echo "$domain_name,$problem_name,,,,,,,$elapsed,TIMEOUT" >> "$OUTPUT_CSV"
        continue
    fi

    if [[ $exit_code -ne 10 && $exit_code -ne 30 ]]; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        echo "ERROR (exit $exit_code)"
        echo "$domain_name,$problem_name,,,,,,,$elapsed,ERROR" >> "$OUTPUT_CSV"
        continue
    fi

    # Check if satisfiable
    if ! echo "$output" | grep -q "SATISFIABLE"; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        echo "UNSAT"
        echo "$domain_name,$problem_name,,,,,,,$elapsed,UNSAT" >> "$OUTPUT_CSV"
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
        category=$(classify_category "$ur_scope" 0 0)
        echo "TIMEOUT (no time for brave)"
        echo "$domain_name,$problem_name,$ur_scope,$ur_struct,,,,$category,$elapsed,TIMEOUT_BRAVE" >> "$OUTPUT_CSV"
        continue
    fi

    # Run brave reasoning for P2/P3 witness aggregation
    brave=$(timeout "${remaining}s" $CLINGO $ENCODINGS "$problem_file" --enum-mode=brave 0 --warn=no-atom-undefined 2>&1)
    brave_exit=$?

    if [[ $brave_exit -eq 124 ]]; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        category=$(classify_category "$ur_scope" 0 0)
        echo "TIMEOUT (brave)"
        echo "$domain_name,$problem_name,$ur_scope,$ur_struct,,,,$category,$elapsed,TIMEOUT_BRAVE" >> "$OUTPUT_CSV"
        continue
    fi

    if [[ $brave_exit -ne 10 && $brave_exit -ne 30 ]]; then
        end_time=$(date +%s.%N)
        elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        category=$(classify_category "$ur_scope" 0 0)
        echo "ERROR (brave exit $brave_exit)"
        echo "$domain_name,$problem_name,$ur_scope,$ur_struct,,,,$category,$elapsed,ERROR_BRAVE" >> "$OUTPUT_CSV"
        continue
    fi

    # Compute P2/P3 measures using shared library
    compute_p2_p3_measures "$brave"

    end_time=$(date +%s.%N)
    elapsed=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
    category=$(classify_category "$ur_scope" "$mx_scope" "$gs_scope")

    echo "($ur_scope,$ur_struct,$mx_scope,$mx_struct,$gs_scope,$gs_struct) [$category] ${elapsed}s"
    echo "$domain_name,$problem_name,$ur_scope,$ur_struct,$mx_scope,$mx_struct,$gs_scope,$gs_struct,$category,$elapsed,OK" >> "$OUTPUT_CSV"
done

echo ""
echo "Results written to $OUTPUT_CSV"

# Summary statistics
total_ok=$(grep -c ",OK$" "$OUTPUT_CSV" || true)
total_timeout=$(grep -c "TIMEOUT" "$OUTPUT_CSV" || true)
total_error=$(grep -c "ERROR" "$OUTPUT_CSV" || true)

echo "Summary: $total_ok OK, $total_timeout timeout, $total_error error"
