#!/bin/bash
# Test experiment runner script
#
# Tests:
# 1. CSV output has correct header
# 2. CSV output has correct number of columns
# 3. Category classification works correctly
# 4. Summary statistics are reported

cd "$(dirname "$0")/.."

EXPERIMENT_RUNNER="tools/run_experiments.sh"
BATCH_TRANSLATOR="tools/batch_translate.py"
SCRATCHPAD="/tmp/thesis-test-experiments-$$"

mkdir -p "$SCRATCHPAD"
trap "rm -rf $SCRATCHPAD" EXIT

passed=0
failed=0

echo "=== Experiment Runner Tests ==="
echo ""

# Setup: Create test problems by translating PDDL
input_dir="$SCRATCHPAD/problems"
mkdir -p "$input_dir"
python $BATCH_TRANSLATOR tests/pddl -o "$input_dir" >/dev/null 2>&1

# Verify we have test files
if [[ $(find "$input_dir" -name "*.lp" -type f | wc -l) -eq 0 ]]; then
    echo "SETUP FAILED: No test problems available"
    exit 1
fi

# Test 1: CSV header format
printf "Test CSV header format...     "
output_csv="$SCRATCHPAD/results.csv"
./tools/run_experiments.sh "$input_dir" "$output_csv" 30 >/dev/null 2>&1

expected_header="domain,problem,i_ur_scope,i_ur_struct,i_mx_scope,i_mx_struct,i_gs_scope,i_gs_struct,category,time_s,status"
actual_header=$(head -1 "$output_csv")

if [[ "$actual_header" == "$expected_header" ]]; then
    echo "PASS"
    passed=$((passed + 1))
else
    echo "FAIL"
    echo "  Expected: $expected_header"
    echo "  Actual:   $actual_header"
    failed=$((failed + 1))
fi

# Test 2: CSV column count (all rows should have 11 fields)
printf "Test CSV column count...      "
bad_rows=0
while IFS= read -r line; do
    # Count commas (11 fields = 10 commas)
    comma_count=$(echo "$line" | tr -cd ',' | wc -c)
    if [[ "$comma_count" -ne 10 ]]; then
        bad_rows=$((bad_rows + 1))
    fi
done < "$output_csv"

if [[ "$bad_rows" -eq 0 ]]; then
    echo "PASS"
    passed=$((passed + 1))
else
    echo "FAIL ($bad_rows rows with wrong column count)"
    failed=$((failed + 1))
fi

# Test 3: Data rows have valid status values
printf "Test status values...         "
valid_statuses="OK|TIMEOUT|TIMEOUT_BRAVE|ERROR|ERROR_BRAVE|UNSAT"
invalid_status=0
tail -n +2 "$output_csv" | while IFS= read -r line; do
    status=$(echo "$line" | awk -F, '{print $NF}')
    if ! echo "$status" | grep -qE "^($valid_statuses)$"; then
        invalid_status=$((invalid_status + 1))
    fi
done

# Check via grep for simplicity
if tail -n +2 "$output_csv" | awk -F, '{print $NF}' | grep -qvE "^($valid_statuses)$"; then
    echo "FAIL (invalid status values)"
    failed=$((failed + 1))
else
    echo "PASS"
    passed=$((passed + 1))
fi

# Test 4: Category classification values
printf "Test category values...       "
valid_categories="2a|2c-sequencing|2c-mutex|undetected"
if tail -n +2 "$output_csv" | awk -F, '{print $9}' | grep -v '^$' | grep -qvE "^($valid_categories)$"; then
    echo "FAIL (invalid category values)"
    failed=$((failed + 1))
else
    echo "PASS"
    passed=$((passed + 1))
fi

# Test 5: Time values are numeric
printf "Test time format...           "
if tail -n +2 "$output_csv" | awk -F, '{print $10}' | grep -v '^$' | grep -qvE '^[0-9]+\.[0-9]+$'; then
    echo "FAIL (non-numeric time values)"
    failed=$((failed + 1))
else
    echo "PASS"
    passed=$((passed + 1))
fi

# Test 6: Script reports summary
printf "Test summary output...        "
summary_output=$(./tools/run_experiments.sh "$input_dir" "$SCRATCHPAD/results2.csv" 30 2>&1)
if echo "$summary_output" | grep -q "Summary:.*OK"; then
    echo "PASS"
    passed=$((passed + 1))
else
    echo "FAIL (no summary)"
    failed=$((failed + 1))
fi

# Test 7: Handles empty directory
printf "Test empty directory...       "
empty_dir="$SCRATCHPAD/empty"
mkdir -p "$empty_dir"
if ./tools/run_experiments.sh "$empty_dir" "$SCRATCHPAD/empty.csv" 5 2>&1 | grep -qi "no.*found\|0 problem"; then
    echo "PASS"
    passed=$((passed + 1))
else
    echo "FAIL"
    failed=$((failed + 1))
fi

echo ""
echo "Results: $passed passed, $failed failed"
exit "$failed"
