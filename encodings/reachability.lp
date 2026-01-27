% Forward Reachability Analysis
% Thesis Reference: Definition 1 (S_reach), Definition 2 (REACH)

#include "../config/defaults.lp".

% ============================================================
% PART 1: Deterministic Reachability Fixpoint (for I_UR)
% ============================================================

reachable_prop(P) :- init(P).
reachable_prop(P) :- operator(O), add(O, P),
    reachable_prop(Q) : precond(O, Q).

% ============================================================
% PART 2: Horizon-Bounded State Exploration
% ============================================================
% Explores execution paths up to a fixed depth using choice rules.
% horizon=20 is sufficient for most planning problems; increase if
% reachable states exist beyond this depth.
% Default horizon is defined in config/defaults.lp

time(0..horizon).

holds(P, 0) :- init(P).

applicable(O, T) :- operator(O), time(T), T < horizon,
    holds(P, T) : precond(O, P).

{ apply(O, T) : applicable(O, T) } 1 :- time(T), T < horizon.

holds(P, T+1) :- holds(P, T), time(T), T < horizon, not deleted(P, T).
deleted(P, T) :- apply(O, T), delete(O, P).
holds(P, T+1) :- apply(O, T), add(O, P).

% ============================================================
% PART 3: Brave Reasoning Predicates
% ============================================================
% These are witnessed in answer sets and aggregated externally.

coexist_witness(G1, G2) :- goal(G1), goal(G2), G1 < G2,
    holds(G1, T), holds(G2, T), time(T).

g2_after_g1_witness(G1, G2) :- goal(G1), goal(G2), G1 != G2,
    holds(G1, T1), holds(G2, T2), T2 >= T1.

% Derive coexist from witnesses (for use by mutex.lp)
coexist(G1, G2) :- coexist_witness(G1, G2).
coexist(G1, G2) :- coexist_witness(G2, G1).

#show reachable_prop/1.
#show coexist_witness/2.
#show g2_after_g1_witness/2.
