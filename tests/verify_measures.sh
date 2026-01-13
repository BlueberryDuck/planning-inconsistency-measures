#!/bin/bash
# Automated verification of all measures against expected values
# Uses brave reasoning for mutex and sequencing measures

cd "$(dirname "$0")/.."

CLINGO=".venv/bin/clingo"
BASE="encodings/planning.lp encodings/reachability.lp"
MEASURES="encodings/measures/unreachability.lp"
EXPECTED_FILE="expected_profiles.txt"

PASSED=0
FAILED=0

while IFS= read -r line; do
	[[ "$line" =~ ^# ]] && continue
	[[ -z "${line// /}" ]] && continue

	scenario=$(echo "$line" | cut -d: -f1 | tr -d ' ')
	values=$(echo "$line" | grep -oP '\(\K[^)]+')
	expected=$(echo "$values" | tr -d ' ')

	echo -n "Testing $scenario... "

	# Part 1: Get unreachability measures (deterministic, 1 answer set)
	UR_OUTPUT=$($CLINGO $BASE $MEASURES scenarios/${scenario}.lp 1 2>&1)
	if echo "$UR_OUTPUT" | grep -q "SATISFIABLE"; then
		UR_SCOPE=$(echo "$UR_OUTPUT" | grep -oP 'i_ur_scope\(\K[0-9]+' | head -1)
		UR_STRUCT=$(echo "$UR_OUTPUT" | grep -oP 'i_ur_struct\(\K[0-9]+' | head -1)
	else
		echo "CLINGO ERROR (unreachability)"
		((FAILED++))
		continue
	fi

	# Part 2: Get brave witnesses for mutex and sequencing
	BRAVE_OUTPUT=$($CLINGO $BASE scenarios/${scenario}.lp --enum-mode=brave 0 2>&1)

	# Parse achievable goals (reachable propositions that are goals)
	REACHABLE=$(echo "$BRAVE_OUTPUT" | grep -oP 'reachable_prop\(\K[^)]+' | sort -u)

	# Parse coexistence witnesses
	COEXIST=$(echo "$BRAVE_OUTPUT" | grep -oP 'coexist_witness\([^)]+\)' | sort -u)

	# Parse g2_after_g1 witnesses
	G2_AFTER=$(echo "$BRAVE_OUTPUT" | grep -oP 'g2_after_g1_witness\([^)]+\)' | sort -u)

	# Get goals for this scenario
	GOALS=$(grep -oP 'goal\(\K[^)]+' scenarios/${scenario}.lp | sort -u)
	readarray -t GOAL_ARRAY <<<"$GOALS"
	GOAL_COUNT=${#GOAL_ARRAY[@]}

	# Compute mutex: achievable goal pairs that DON'T coexist
	MX_SCOPE=0
	MX_STRUCT=0
	declare -A IN_MUTEX

	for ((i = 0; i < GOAL_COUNT; i++)); do
		for ((j = i + 1; j < GOAL_COUNT; j++)); do
			g1="${GOAL_ARRAY[$i]}"
			g2="${GOAL_ARRAY[$j]}"
			[[ -z "$g1" || -z "$g2" ]] && continue

			# Check if both achievable
			g1_reach=$(echo "$REACHABLE" | grep -cxF "$g1")
			g2_reach=$(echo "$REACHABLE" | grep -cxF "$g2")

			if [ "$g1_reach" -gt 0 ] && [ "$g2_reach" -gt 0 ]; then
				# Check coexistence (try both orderings)
				if ! echo "$COEXIST" | grep -qE "coexist_witness\($g1,$g2\)|coexist_witness\($g2,$g1\)"; then
					((MX_STRUCT++))
					IN_MUTEX["$g1"]=1
					IN_MUTEX["$g2"]=1
				fi
			fi
		done
	done
	MX_SCOPE=${#IN_MUTEX[@]}

	# Compute sequencing conflicts: achievable ordered pairs where g2 NOT reachable after g1
	GS_SCOPE=0
	GS_STRUCT=0
	declare -A IN_SEQ

	for ((i = 0; i < GOAL_COUNT; i++)); do
		for ((j = 0; j < GOAL_COUNT; j++)); do
			[[ $i -eq $j ]] && continue
			g1="${GOAL_ARRAY[$i]}"
			g2="${GOAL_ARRAY[$j]}"
			[[ -z "$g1" || -z "$g2" ]] && continue

			g1_reach=$(echo "$REACHABLE" | grep -cxF "$g1")
			g2_reach=$(echo "$REACHABLE" | grep -cxF "$g2")

			if [ "$g1_reach" -gt 0 ] && [ "$g2_reach" -gt 0 ]; then
				# Check if g2 reachable after g1
				if ! echo "$G2_AFTER" | grep -q "g2_after_g1_witness($g1,$g2)"; then
					((GS_STRUCT++))
					IN_SEQ["$g1"]=1
					IN_SEQ["$g2"]=1
				fi
			fi
		done
	done
	GS_SCOPE=${#IN_SEQ[@]}

	actual="$UR_SCOPE,$UR_STRUCT,$MX_SCOPE,$MX_STRUCT,$GS_SCOPE,$GS_STRUCT"

	if [ "$actual" = "$expected" ]; then
		echo "PASS ($actual)"
		((PASSED++))
	else
		echo "FAIL"
		echo "  Expected: $expected"
		echo "  Actual:   $actual"
		((FAILED++))
	fi

	unset IN_MUTEX
	unset IN_SEQ
done <"$EXPECTED_FILE"

echo ""
echo "Results: $PASSED passed, $FAILED failed"
exit $FAILED
