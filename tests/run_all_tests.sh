#!/bin/bash
# Master test runner for thesis planning measures
#
# Runs all test suites and reports aggregate results.
#
# Usage:
#   ./tests/run_all_tests.sh [test_name...]
#
# Examples:
#   ./tests/run_all_tests.sh              # Run all tests
#   ./tests/run_all_tests.sh measures     # Run only measure tests
#   ./tests/run_all_tests.sh translator batch  # Run specific tests

cd "$(dirname "$0")/.."

# Colors for output (if terminal supports it)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

# Available test suites
declare -A test_suites=(
    ["measures"]="tests/test_measures.sh"
    ["translator"]="tests/test_translator.sh"
    ["batch"]="tests/test_batch_translate.sh"
    ["experiments"]="tests/test_experiment_runner.sh"
)

# Parse arguments
if [[ $# -gt 0 ]]; then
    selected_tests=("$@")
else
    selected_tests=("measures" "translator" "batch" "experiments")
fi

echo "=============================================="
echo "  Thesis Planning Measures - Test Suite"
echo "=============================================="
echo ""

total_passed=0
total_failed=0
suite_results=()

for suite_name in "${selected_tests[@]}"; do
    script="${test_suites[$suite_name]}"
    
    if [[ -z "$script" ]]; then
        echo -e "${YELLOW}Warning: Unknown test suite '$suite_name'${NC}"
        echo "Available: ${!test_suites[*]}"
        echo ""
        continue
    fi
    
    if [[ ! -x "$script" ]]; then
        chmod +x "$script"
    fi
    
    echo "----------------------------------------------"
    echo "Running: $suite_name"
    echo "----------------------------------------------"
    echo ""
    
    # Run test and capture output
    output=$("$script" 2>&1)
    exit_code=$?
    
    echo "$output"
    echo ""
    
    # Parse results from output
    if echo "$output" | grep -q "Results:"; then
        results_line=$(echo "$output" | grep "Results:" | tail -1)
        passed=$(echo "$results_line" | grep -oP '\d+(?= passed)')
        failed=$(echo "$results_line" | grep -oP '\d+(?= failed)')
        
        [[ -z "$passed" ]] && passed=0
        [[ -z "$failed" ]] && failed=0
        
        total_passed=$((total_passed + passed))
        total_failed=$((total_failed + failed))
        
        if [[ "$failed" -eq 0 ]]; then
            suite_results+=("${GREEN}PASS${NC} $suite_name ($passed tests)")
        else
            suite_results+=("${RED}FAIL${NC} $suite_name ($passed passed, $failed failed)")
        fi
    else
        # Couldn't parse results
        if [[ $exit_code -eq 0 ]]; then
            suite_results+=("${GREEN}PASS${NC} $suite_name")
        else
            suite_results+=("${RED}FAIL${NC} $suite_name (exit code $exit_code)")
            total_failed=$((total_failed + 1))
        fi
    fi
done

echo "=============================================="
echo "  Summary"
echo "=============================================="
echo ""

for result in "${suite_results[@]}"; do
    echo -e "  $result"
done

echo ""
echo "----------------------------------------------"
echo -e "Total: ${GREEN}$total_passed passed${NC}, ${RED}$total_failed failed${NC}"
echo "----------------------------------------------"

if [[ $total_failed -eq 0 ]]; then
    echo -e "\n${GREEN}All tests passed!${NC}\n"
    exit 0
else
    echo -e "\n${RED}Some tests failed.${NC}\n"
    exit 1
fi
