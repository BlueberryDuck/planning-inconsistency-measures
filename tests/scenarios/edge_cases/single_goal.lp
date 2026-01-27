% Single Goal Scenario (Edge Case)
% Expected: (0, 0, 0, 0, 0, 0)
% Mutex and sequencing require pairs (G1 != G2), so single goal = 0.

init(ready).
goal(ready).

% Dummy operator
precond(noop, ready).
add(noop, done).
