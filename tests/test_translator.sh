#!/bin/bash
# Test PDDL to ASP translator
#
# Tests:
# 1. Translation produces valid ASP (clingo can parse it)
# 2. Translated PDDL produces same measures as hand-crafted ASP scenarios
#
# Uses PDDL files in tests/pddl/ and compares against tests/scenarios/

cd "$(dirname "$0")/.."

source tools/lib/aggregate_witnesses.sh

CLINGO=".venv/bin/clingo"
PYTHON=".venv/bin/python"
TRANSLATOR="tools/pddl_to_asp.py"
ENCODINGS="encodings/planning.lp encodings/reachability.lp"
MEASURES="encodings/measures/unreachability.lp encodings/measures/mutex.lp encodings/measures/sequencing.lp"
SCRATCHPAD="/tmp/thesis-test-translator-$$"

mkdir -p "$SCRATCHPAD"
trap "rm -rf $SCRATCHPAD" EXIT

passed=0
failed=0

echo "=== PDDL Translator Tests ==="
echo ""

# Test cases: (subdir, expected_profile, asp_scenario_for_comparison)
declare -a test_cases=(
    "locked_door:1,3,0,0,0,0:p1_unreachability/locked_door"
    "trust_travel:0,0,2,1,2,1:mixed/trust_travel"
)

for test_case in "${test_cases[@]}"; do
    IFS=':' read -r test_name expected scenario_path <<< "$test_case"

    printf "Testing %-20s " "$test_name..."

    domain_path="tests/pddl/$test_name/domain.pddl"
    problem_path="tests/pddl/$test_name/problem01.pddl"
    output_path="$SCRATCHPAD/${test_name}.lp"

    # Check PDDL files exist
    if [[ ! -f "$domain_path" || ! -f "$problem_path" ]]; then
        echo "SKIP (PDDL files missing)"
        continue
    fi

    # Test 1: Translation succeeds
    if ! $PYTHON $TRANSLATOR "$domain_path" "$problem_path" -o "$output_path" 2>/dev/null; then
        echo "FAIL (translation error)"
        failed=$((failed + 1))
        continue
    fi

    # Test 2: Clingo can parse the output (use 1 solution, not 0 which enumerates all)
    if ! $CLINGO $ENCODINGS $MEASURES "$output_path" 1 --warn=no-atom-undefined 2>&1 | grep -q "SATISFIABLE\|UNSATISFIABLE"; then
        echo "FAIL (clingo parse error)"
        failed=$((failed + 1))
        continue
    fi

    # Test 3: Compute measures from translated PDDL
    output=$($CLINGO $ENCODINGS $MEASURES "$output_path" 1 --warn=no-atom-undefined 2>&1)

    if ! echo "$output" | grep -q "SATISFIABLE"; then
        echo "FAIL (not satisfiable)"
        failed=$((failed + 1))
        continue
    fi

    # Extract P1 measures
    ur_scope=$(echo "$output" | grep -oP 'i_ur_scope\(\K[0-9]+' | head -1)
    ur_struct=$(echo "$output" | grep -oP 'i_ur_struct\(\K[0-9]+' | head -1)
    [[ -z "$ur_scope" ]] && ur_scope=0
    [[ -z "$ur_struct" ]] && ur_struct=0

    # Run brave reasoning for P2/P3
    brave=$($CLINGO $ENCODINGS "$output_path" --enum-mode=brave 0 --warn=no-atom-undefined 2>&1)
    compute_p2_p3_measures "$brave"

    actual="$ur_scope,$ur_struct,$mx_scope,$mx_struct,$gs_scope,$gs_struct"

    # Test 4: Compare with expected profile
    if [[ "$actual" == "$expected" ]]; then
        echo "PASS ($actual)"
        passed=$((passed + 1))
    else
        echo "FAIL"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        failed=$((failed + 1))
    fi
done

echo ""
echo "=== Translation Syntax Tests ==="
echo ""

# Test that translator handles edge cases
for domain_file in tests/pddl/*/domain.pddl; do
    [[ -f "$domain_file" ]] || continue
    test_dir=$(dirname "$domain_file")
    base=$(basename "$test_dir")

    # Find first problem file
    problem=$(find "$test_dir" -name "problem*.pddl" -o -name "p[0-9]*.pddl" | head -1)
    [[ -f "$problem" ]] || continue

    printf "Syntax check %-15s " "$base..."

    output_path="$SCRATCHPAD/${base}_syntax.lp"

    if $PYTHON $TRANSLATOR "$domain_file" "$problem" -o "$output_path" 2>/dev/null; then
        # Verify output contains expected sections
        if grep -q "^init\|^goal\|^precond\|^add" "$output_path"; then
            echo "PASS"
            passed=$((passed + 1))
        else
            echo "FAIL (missing predicates)"
            failed=$((failed + 1))
        fi
    else
        echo "FAIL (translation error)"
        failed=$((failed + 1))
    fi
done

echo ""
echo "Results: $passed passed, $failed failed"
exit "$failed"
