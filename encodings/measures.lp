% P1 Unreachability Measures
%
% Computes P1 (Unreachability Profile) deterministically.
% P2 (Mutex) and P3 (Sequencing) are computed in Python from brave witnesses.

% ============================================================
% P1: Unreachability Profile
% ============================================================

% Unreachable Goal Propositions
unreachable_goal(G) :- goal(G), not reachable_prop(G).
i_ur_scope(N) :- N = #count{ G : unreachable_goal(G) }.

% Total Unreachable Propositions
unreachable(P) :- prop(P), not reachable_prop(P).
i_ur_struct(N) :- N = #count{ P : unreachable(P) }.

% ============================================================
% Output
% ============================================================
#show goal/1.
#show reachable_prop/1.
#show i_ur_scope/1.
#show i_ur_struct/1.
