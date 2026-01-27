% Light Switch Scenario (Reversible Mutex)
% Expected: (0, 0, 2, 1, 0, 0)

init(off).
goal(on).
goal(off).

% turn_on: {off} -> {on}, delete {off}
precond(turn_on, off).
add(turn_on, on).
delete(turn_on, off).

% turn_off: {on} -> {off}, delete {on}
precond(turn_off, on).
add(turn_off, off).
delete(turn_off, on).
