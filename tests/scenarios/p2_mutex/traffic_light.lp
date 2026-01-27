% Traffic Light Scenario (Mutex Clique)
% Expected: (0, 0, 3, 3, 0, 0)

init(red).
goal(red).
goal(yellow).
goal(green).

% Cyclic transitions: red -> green -> yellow -> red
precond(to_green, red).
add(to_green, green).
delete(to_green, red).

precond(to_yellow, green).
add(to_yellow, yellow).
delete(to_yellow, green).

precond(to_red, yellow).
add(to_red, red).
delete(to_red, yellow).
