% Empty Goals Scenario (Edge Case)
% Expected: (0, 0, 0, 0, 0, 0)
% No goals means all measures are trivially 0.

init(start).

% Dummy operator
precond(step, start).
add(step, end).
