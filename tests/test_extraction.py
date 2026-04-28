"""Unit tests for the extraction layer (brave-output -> MeasureProfile / ProblemSize).

These tests do NOT invoke Clingo. They construct synthetic BraveOutcome objects
and assert the pure extraction logic.
"""

from planning_measures.extraction import (
    KEEP_ATOMS,
    BraveOutcome,
    collect,
    extract_measures,
    extract_problem_size,
)
from planning_measures.profile import MeasureProfile, ProblemSize


def _outcome(
    *,
    goals=(),
    props=(),
    operators=(),
    true_reachable=(),
    coexist_witness=(),
    g2_after_g1_witness=(),
) -> BraveOutcome:
    return BraveOutcome(
        goals=frozenset(goals),
        props=frozenset(props),
        operators=frozenset(operators),
        true_reachable=frozenset(true_reachable),
        coexist_witness=frozenset(coexist_witness),
        g2_after_g1_witness=frozenset(g2_after_g1_witness),
    )


class TestExtractMeasuresEmpty:
    def test_empty_outcome_yields_zero_profile(self):
        profile = extract_measures(_outcome())
        assert profile == MeasureProfile(0, 0, 0, 0, 0, 0)


class TestExtractMeasuresUnreachability:
    def test_unreachable_goal_counted_in_ur_scope(self):
        profile = extract_measures(
            _outcome(
                goals=("g1", "g2"),
                props=("g1", "g2", "p"),
                true_reachable=("g1", "p"),  # g2 unreachable
            )
        )
        assert profile.ur_scope == 1
        assert profile.ur_struct == 1  # only g2 unreachable among props

    def test_ur_struct_counts_all_unreachable_props(self):
        profile = extract_measures(
            _outcome(
                goals=("g1",),
                props=("g1", "p", "q", "r"),
                true_reachable=("p",),
            )
        )
        assert profile.ur_scope == 1
        assert profile.ur_struct == 3  # g1, q, r unreachable


class TestExtractMeasuresMutex:
    def test_two_achievable_goals_no_witness_either_direction_are_mutex(self):
        profile = extract_measures(
            _outcome(
                goals=("g1", "g2"),
                true_reachable=("g1", "g2"),
                # no coexist witnesses
            )
        )
        assert profile.mx_scope == 2
        assert profile.mx_struct == 1

    def test_witness_in_reverse_direction_is_still_coexistence(self):
        """Witness (g2,g1) means the goals coexisted; symmetric check must NOT mark mutex."""
        profile = extract_measures(
            _outcome(
                goals=("g1", "g2"),
                true_reachable=("g1", "g2"),
                coexist_witness=(("g2", "g1"),),
            )
        )
        assert profile.mx_scope == 0
        assert profile.mx_struct == 0

    def test_unreachable_goals_excluded_from_mutex(self):
        """Mutex is over achievable goals only."""
        profile = extract_measures(
            _outcome(
                goals=("g1", "g2"),
                true_reachable=("g1",),  # g2 unreachable
                # no witnesses
            )
        )
        assert profile.ur_scope == 1
        assert profile.mx_scope == 0  # not counted: g2 not achievable
        assert profile.mx_struct == 0

    def test_three_goals_one_pair_mutex(self):
        profile = extract_measures(
            _outcome(
                goals=("a", "b", "c"),
                true_reachable=("a", "b", "c"),
                coexist_witness=(("a", "b"), ("a", "c")),  # b<->c missing
            )
        )
        assert profile.mx_scope == 2  # b and c
        assert profile.mx_struct == 1


class TestExtractMeasuresSequencing:
    def test_sequencing_is_directional(self):
        """Witness (a,b) means b reachable after a; (b,a) is a separate ordered pair."""
        profile = extract_measures(
            _outcome(
                goals=("a", "b"),
                true_reachable=("a", "b"),
                coexist_witness=(("a", "b"),),  # not mutex
                g2_after_g1_witness=(
                    ("a", "b"),
                ),  # b reachable after a, but a after b missing
            )
        )
        # ordered conflicts: (b,a) is the only conflict
        assert profile.gs_struct == 1
        assert profile.gs_scope == 2  # a and b both involved

    def test_three_goals_one_witness_yields_five_conflicts(self):
        profile = extract_measures(
            _outcome(
                goals=("a", "b", "c"),
                true_reachable=("a", "b", "c"),
                coexist_witness=(  # all coexist (so no mutex)
                    ("a", "b"),
                    ("a", "c"),
                    ("b", "c"),
                ),
                g2_after_g1_witness=(("a", "b"),),  # only a->b works
            )
        )
        # ordered pairs (g1,g2) g1!=g2: (a,b)(a,c)(b,a)(b,c)(c,a)(c,b) = 6 total
        # only (a,b) has witness; so 5 conflicts
        assert profile.gs_struct == 5
        assert profile.gs_scope == 3


class TestExtractProblemSize:
    def test_cardinalities_from_raw_atom_sets(self):
        size = extract_problem_size(
            _outcome(
                goals=("g1", "g2"),
                props=("g1", "g2", "p", "q"),
                operators=("o1", "o2", "o3"),
            )
        )
        assert size == ProblemSize(num_goals=2, num_props=4, num_operators=3)

    def test_empty_outcome_zero_size(self):
        assert extract_problem_size(_outcome()) == ProblemSize(0, 0, 0)


class TestKeepAtoms:
    def test_keep_atoms_lists_canonical_atom_names(self):
        assert KEEP_ATOMS == frozenset(
            {
                "goal",
                "prop",
                "operator",
                "true_reachable",
                "coexist_witness",
                "g2_after_g1_witness",
            }
        )


class TestCollect:
    def test_collect_buckets_into_typed_outcome(self):
        buckets = {
            "goal": [("g1",), ("g2",)],
            "prop": [("g1",), ("g2",), ("p",)],
            "operator": [("o1",)],
            "true_reachable": [("g1",), ("p",)],
            "coexist_witness": [("g1", "g2")],
            "g2_after_g1_witness": [("g1", "g2"), ("g2", "g1")],
        }
        outcome = collect(buckets)

        assert outcome.goals == frozenset({"g1", "g2"})
        assert outcome.props == frozenset({"g1", "g2", "p"})
        assert outcome.operators == frozenset({"o1"})
        assert outcome.true_reachable == frozenset({"g1", "p"})
        assert outcome.coexist_witness == frozenset({("g1", "g2")})
        assert outcome.g2_after_g1_witness == frozenset({("g1", "g2"), ("g2", "g1")})

    def test_collect_missing_keys_default_empty(self):
        """A bucket dict with no entries for a key yields empty frozenset."""
        outcome = collect({})
        assert outcome.goals == frozenset()
        assert outcome.coexist_witness == frozenset()
