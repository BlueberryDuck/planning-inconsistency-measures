% Goal Sequencing Conflict Profile (P3)
% Thesis Reference: Definition 8, 9, 10

% achievable_goal(G) defined in mutex.lp
% g2_after_g1(G1, G2) defined in reachability.lp

% Definition 8: Sequencing conflict (ordered pairs)
% G1 -> G2 conflict if G2 cannot be reached after achieving G1
seq_conflict(G1, G2) :- achievable_goal(G1), achievable_goal(G2), G1 != G2,
    not g2_after_g1(G1, G2).

% Definition 9: Goals involved in sequencing conflict
in_seq_conflict(G) :- seq_conflict(G, _).
in_seq_conflict(G) :- seq_conflict(_, G).
i_gs_scope(N) :- N = #count{ G : in_seq_conflict(G) }.

% Definition 10: Sequencing conflict pair count
i_gs_struct(N) :- N = #count{ G1, G2 : seq_conflict(G1, G2) }.

#show i_gs_scope/1.
#show i_gs_struct/1.
