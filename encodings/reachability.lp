% Forward Reachability Analysis
% Thesis Reference: Definition 1 (S_reach), Definition 2 (REACH)

% ============================================================
% PART 1: Deterministic reachability fixpoint (for I_UR)
% ============================================================

reachable_prop(P) :- init(P).
reachable_prop(P) :- operator(O), add(O, P),
    reachable_prop(Q) : precond(O, Q).

% ============================================================
% PART 2: Explicit state space exploration
% ============================================================
% Represent states as integers, track which props hold in each state.
% This gives us ALL reachable states, not just one execution path.

% State 0 = initial state
state(0).
in_state(P, 0) :- init(P).

% Generate successor states
% For each state S and applicable operator O, create successor state
#const max_states = 100.
potential_state(1..max_states).

% Check operator applicability in a state
op_applicable(O, S) :- state(S), operator(O),
    in_state(P, S) : precond(O, P).

% Successor state contents after applying O in S
% RESULT(s,o) = (s \ delete(o)) ∪ add(o)
succ_has(S, O, P) :- op_applicable(O, S), in_state(P, S), not delete(O, P).
succ_has(S, O, P) :- op_applicable(O, S), add(O, P).

% Match successor to existing or new state
% Two states are equal if they have exactly the same propositions
states_differ(S1, S2) :- state(S1), state(S2), in_state(P, S1), not in_state(P, S2).
states_differ(S1, S2) :- state(S1), state(S2), in_state(P, S2), not in_state(P, S1).
states_equal(S1, S2) :- state(S1), state(S2), not states_differ(S1, S2).

% Successor matches existing state
succ_matches_existing(S, O, S2) :- op_applicable(O, S), state(S2),
    not succ_differs_from(S, O, S2).
succ_differs_from(S, O, S2) :- op_applicable(O, S), state(S2), succ_has(S, O, P), not in_state(P, S2).
succ_differs_from(S, O, S2) :- op_applicable(O, S), state(S2), in_state(P, S2), not succ_has(S, O, P).

% Create new state if successor doesn't match any existing state
needs_new_state(S, O) :- op_applicable(O, S), not succ_matches_existing(S, O, _).

% Assign new state IDs (this is tricky in pure ASP)
% Simpler approach: just track which prop-combinations are reachable

% ============================================================
% ALTERNATIVE: Track reachable prop-combinations directly
% ============================================================

% A state signature is the set of props that hold
% Track which combinations are reachable via time-based exploration
% but UNION across all paths (brave reasoning)

#const horizon = 20.
time(0..horizon).

holds(P, 0) :- init(P).

applicable(O, T) :- operator(O), time(T), T < horizon,
    holds(P, T) : precond(O, P).

{ apply(O, T) : applicable(O, T) } 1 :- time(T), T < horizon.

holds(P, T+1) :- holds(P, T), time(T), T < horizon, not deleted(P, T).
deleted(P, T) :- apply(O, T), delete(O, P).
holds(P, T+1) :- apply(O, T), add(O, P).

% ============================================================
% PART 3: Brave predicates (shown in output, aggregated externally)
% ============================================================

% These are BRAVE: true in this answer set if witnessed
coexist_witness(G1, G2) :- goal(G1), goal(G2), G1 < G2,
    holds(G1, T), holds(G2, T), time(T).

g2_after_g1_witness(G1, G2) :- goal(G1), goal(G2), G1 != G2,
    holds(G1, T1), holds(G2, T2), T2 >= T1.

#show reachable_prop/1.
#show coexist_witness/2.
#show g2_after_g1_witness/2.
