% Forward Reachability Analysis
%
% Computes:
% 1. State exploration traces (non-deterministic, up to horizon)
% 2. Brave reasoning witnesses for mutex/sequencing
% 3. True reachability from state exploration

#const horizon = 20.

% ============================================================
% PART 1: State Space Exploration (Non-deterministic)
% ============================================================
% Explores execution traces up to `horizon` steps.
% Different answer sets correspond to different execution paths.

time(0..horizon).

holds(P, 0) :- init(P).

neg_precond_violated(O, T) :- neg_precond(O, P), holds(P, T), time(T).
applicable(O, T) :- operator(O), time(T), T < horizon,
    not neg_precond_violated(O, T),
    holds(P, T) : precond(O, P).

{ apply(O, T) : applicable(O, T) } 1 :- time(T), T < horizon.

holds(P, T+1) :- holds(P, T), time(T), T < horizon, not deleted(P, T).
deleted(P, T) :- apply(O, T), delete(O, P).
holds(P, T+1) :- apply(O, T), add(O, P).

% ============================================================
% PART 2: Witnesses for Brave Reasoning
% ============================================================
% Under --enum-mode=brave, clingo returns the union of atoms
% across all answer sets. Absence of a witness means the
% condition is never satisfiable in any execution path.

coexist_witness(G1, G2) :- goal(G1), goal(G2), G1 < G2,
    holds(G1, T), holds(G2, T), time(T).

g2_after_g1_witness(G1, G2) :- goal(G1), goal(G2), G1 != G2,
    holds(G1, T1), holds(G2, T2), T2 >= T1.

% ============================================================
% PART 3: True Reachability
% ============================================================
% Under brave reasoning, a proposition is truly reachable if
% it appears in any state of any trace up to the horizon.

true_reachable(P) :- holds(P, T), prop(P).

#show coexist_witness/2.
#show g2_after_g1_witness/2.
#show true_reachable/1.
