% Goal Mutex Profile (P2)
% Thesis Reference: Definition 5, 6, 7

% Achievable: goal becomes true at some time step
achievable_goal(G) :- goal(G), reachable_prop(G).

% coexist(G1, G2) derived from brave witnesses in reachability.lp
goals_coexist(G1, G2) :- goal(G1), goal(G2), G1 != G2, coexist(G1, G2).

% Definition 5: Mutex = both achievable but never coexist
% Use G1 < G2 for unordered pairs (mutex is symmetric)
mutex(G1, G2) :- achievable_goal(G1), achievable_goal(G2), G1 < G2,
    not goals_coexist(G1, G2), not goals_coexist(G2, G1).

% Definition 6: Goals involved in mutex
in_mutex(G) :- mutex(G, _).
in_mutex(G) :- mutex(_, G).
i_mx_scope(N) :- N = #count{ G : in_mutex(G) }.

% Definition 7: Mutex pair count
i_mx_struct(N) :- N = #count{ G1, G2 : mutex(G1, G2) }.

#show i_mx_scope/1.
#show i_mx_struct/1.
