% Forward Reachability Analysis
%
% Computes:
% 1. Reachable propositions (deterministic fixpoint for P1)
% 2. State exploration witnesses (brave reasoning for P2/P3)

#const horizon = 20.

% ============================================================
% PART 1: Proposition Reachability (Deterministic)
% ============================================================
% A proposition is reachable if it's initially true OR some operator
% can produce it and all that operator's preconditions are reachable.
%
% This is a monotonic fixpoint computed in a single grounding pass.
% Used for P1 unreachability measure.

reachable_prop(P) :- init(P).
reachable_prop(P) :- operator(O), add(O, P),
    reachable_prop(Q) : precond(O, Q).

% ============================================================
% PART 2: State Space Exploration (Non-deterministic)
% ============================================================
% Explores execution traces up to `horizon` steps.
% Different answer sets = different execution paths.
% Used to generate witnesses for P2 (mutex) and P3 (sequencing).

time(0..horizon).

% Initial state
holds(P, 0) :- init(P).

% Operator applicability: all preconditions must hold
applicable(O, T) :- operator(O), time(T), T < horizon,
    holds(P, T) : precond(O, P).

% Non-deterministic choice: apply at most one operator per step
{ apply(O, T) : applicable(O, T) } 1 :- time(T), T < horizon.

% Frame axiom: propositions persist unless deleted
holds(P, T+1) :- holds(P, T), time(T), T < horizon, not deleted(P, T).
deleted(P, T) :- apply(O, T), delete(O, P).

% Effect application
holds(P, T+1) :- apply(O, T), add(O, P).

% ============================================================
% PART 3: Witnesses for Brave Reasoning
% ============================================================
% Under --enum-mode=brave, clingo returns the UNION of atoms from
% ALL answer sets. Absence of a witness means the condition is
% NEVER satisfiable in ANY execution path.

% Witness: G1 and G2 hold simultaneously at some time
% If absent: goals are MUTEX (can never coexist)
coexist_witness(G1, G2) :- goal(G1), goal(G2), G1 < G2,
    holds(G1, T), holds(G2, T), time(T).

% Witness: G2 is achieved at time >= when G1 is achieved
% If absent: SEQUENCING CONFLICT (achieving G1 blocks G2 forever)
g2_after_g1_witness(G1, G2) :- goal(G1), goal(G2), G1 != G2,
    holds(G1, T1), holds(G2, T2), T2 >= T1.

% Output for Python
#show coexist_witness/2.
#show g2_after_g1_witness/2.
