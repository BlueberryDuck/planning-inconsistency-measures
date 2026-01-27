% Coexisting Goals Scenario (No Mutex)
% Expected: (0, 0, 0, 0, 0, 0)
% Both goals are initially true and can coexist trivially.

init(a).
init(b).
goal(a).
goal(b).

% Optional operator (goals already satisfied)
precond(toggle, a).
add(toggle, c).
