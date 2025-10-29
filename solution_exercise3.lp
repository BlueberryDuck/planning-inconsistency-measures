% Define all propositions in the domain
proposition(at_location_a).
proposition(at_location_b).
proposition(door_open).
proposition(door_closed).
proposition(on_mars).  % Should be unreachable - no action achieves this!

% Initial state: what's true at the beginning
initially(at_location_a).
initially(door_closed).

% Define actions and what they achieve
action(move_to_b).
achieves(move_to_b, at_location_b).

action(open_door).
achieves(open_door, door_open).

:- move_to_b, door_closed.

% TODO: Define reachable/1 rule
% Hint: A proposition is reachable if it's initially true OR some action achieves it
reachable(X) :- initially(X).
reachable(Y) :- action(A), achieves(A, Y).
reachable(Z) :- reachable(Y), action(A), achieves(A, Z).

% TODO: Define unreachable/1 rule  
% Hint: A proposition is unreachable if it's a proposition but NOT reachable
unreachable(X) :- proposition(X), not reachable(X).

#show unreachable/1.
#show reachable/1.
