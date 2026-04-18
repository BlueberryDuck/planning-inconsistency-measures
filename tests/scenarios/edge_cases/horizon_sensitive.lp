% Horizon Sensitivity Scenario (Edge Case)
%
% A chain of 3 operators: a -> b -> c -> d
% The goal (d) requires 3 steps to reach. With horizon < 3,
% d appears unreachable. With horizon >= 3, d is reachable
% and the profile is consistent.
%
% Expected at horizon=2: (1, 1, 0, 0, 0, 0) - d unreachable
% Expected at horizon=3: (0, 0, 0, 0, 0, 0) - consistent

init(a).
goal(d).

% o1: a -> b
precond(o1, a).
add(o1, b).

% o2: b -> c
precond(o2, b).
add(o2, c).

% o3: c -> d
precond(o3, c).
add(o3, d).
