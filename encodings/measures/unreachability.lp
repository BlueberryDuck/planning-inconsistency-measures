% Unreachability Profile (P1)
% Thesis Reference: Definition 3, Definition 4

% reachable_prop(P) is defined in reachability.lp

% Definition 3: Unreachable Goal Propositions Count
unreachable_goal(G) :- goal(G), not reachable_prop(G).
i_ur_scope(N) :- N = #count{ G : unreachable_goal(G) }.

% Definition 4: Total Unreachable Propositions Count
unreachable(P) :- prop(P), not reachable_prop(P).
i_ur_struct(N) :- N = #count{ P : unreachable(P) }.

#show i_ur_scope/1.
#show i_ur_struct/1.
