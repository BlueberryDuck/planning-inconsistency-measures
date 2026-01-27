#!/bin/bash
# Test batch PDDL translator
#
# Tests:
# 1. Dry-run mode works and finds PDDL pairs
# 2. Actual translation produces valid output files
# 3. Handles various directory structures

cd "$(dirname "$0")/.."

PYTHON=".venv/bin/python"
BATCH_TRANSLATOR="tools/batch_translate.py"
SCRATCHPAD="/tmp/thesis-test-batch-$$"

mkdir -p "$SCRATCHPAD"
trap "rm -rf $SCRATCHPAD" EXIT

passed=0
failed=0

echo "=== Batch Translator Tests ==="
echo ""

# Test 1: Dry-run on tests/pddl directory
printf "Test dry-run mode...          "
output=$($PYTHON $BATCH_TRANSLATOR tests/pddl --dry-run 2>&1)
if echo "$output" | grep -q "Found [0-9]* PDDL"; then
    count=$(echo "$output" | grep -oP 'Found \K[0-9]+')
    if [[ "$count" -ge 1 ]]; then
        echo "PASS (found $count pairs)"
        passed=$((passed + 1))
    else
        echo "FAIL (no pairs found)"
        failed=$((failed + 1))
    fi
else
    echo "FAIL (unexpected output)"
    failed=$((failed + 1))
fi

# Test 2: Actual translation to temp directory
printf "Test actual translation...    "
output_dir="$SCRATCHPAD/translated"
if $PYTHON $BATCH_TRANSLATOR tests/pddl -o "$output_dir" 2>&1 | grep -q "translated"; then
    # Check that files were created
    file_count=$(find "$output_dir" -name "*.lp" -type f 2>/dev/null | wc -l)
    if [[ "$file_count" -ge 1 ]]; then
        echo "PASS ($file_count files)"
        passed=$((passed + 1))
    else
        echo "FAIL (no output files)"
        failed=$((failed + 1))
    fi
else
    echo "FAIL (translation failed)"
    failed=$((failed + 1))
fi

# Test 3: Translated files are valid ASP
printf "Test output validity...       "
valid=0
invalid=0
for lp_file in "$output_dir"/*.lp; do
    [[ -f "$lp_file" ]] || continue
    if grep -q "^init\|^goal\|^precond\|^add" "$lp_file"; then
        valid=$((valid + 1))
    else
        invalid=$((invalid + 1))
    fi
done

if [[ "$valid" -gt 0 && "$invalid" -eq 0 ]]; then
    echo "PASS ($valid valid files)"
    passed=$((passed + 1))
    elif [[ "$valid" -gt 0 ]]; then
    echo "PARTIAL ($valid valid, $invalid invalid)"
    failed=$((failed + 1))
else
    echo "FAIL (no valid files)"
    failed=$((failed + 1))
fi

# Test 4: Test with nested directory structure
printf "Test nested directories...    "
nested_dir="$SCRATCHPAD/nested"
mkdir -p "$nested_dir/domain1"
cp tests/pddl/locked_door/domain.pddl "$nested_dir/domain1/domain.pddl"
cp tests/pddl/locked_door/problem01.pddl "$nested_dir/domain1/p01.pddl"

output_dir2="$SCRATCHPAD/translated2"
if $PYTHON $BATCH_TRANSLATOR "$nested_dir" -o "$output_dir2" 2>&1 | grep -q "translated"; then
    if [[ -f "$output_dir2/domain1_p01.lp" ]]; then
        echo "PASS"
        passed=$((passed + 1))
    else
        # Check for any .lp file
        if find "$output_dir2" -name "*.lp" -type f | grep -q .; then
            echo "PASS (different naming)"
            passed=$((passed + 1))
        else
            echo "FAIL (no output)"
            failed=$((failed + 1))
        fi
    fi
else
    echo "FAIL"
    failed=$((failed + 1))
fi

# Test 5: Non-existent directory
printf "Test missing directory...     "
if $PYTHON $BATCH_TRANSLATOR /nonexistent/path 2>&1 | grep -qi "error\|not found"; then
    echo "PASS (error reported)"
    passed=$((passed + 1))
else
    echo "FAIL (no error)"
    failed=$((failed + 1))
fi

# Test 6: Verbose mode
printf "Test verbose mode...          "
if $PYTHON $BATCH_TRANSLATOR tests/pddl -o "$SCRATCHPAD/verbose_out" -v 2>&1 | grep -q "OK:"; then
    echo "PASS"
    passed=$((passed + 1))
else
    echo "FAIL"
    failed=$((failed + 1))
fi

echo ""
echo "Results: $passed passed, $failed failed"
exit "$failed"
