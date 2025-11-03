% ==============================================================================
% EXAMPLE 2B: True Constraints - Eliminating Answer Sets
% ==============================================================================
% This shows the difference between DERIVING conflicts vs ELIMINATING solutions
% ==============================================================================

% Same setup as example2
goal(robot_at_a).
goal(robot_at_b).
goal(door_open).
goal(door_closed).

mutex(robot_at_a, robot_at_b).
mutex(robot_at_b, robot_at_a).
mutex(door_open, door_closed).
mutex(door_closed, door_open).

% TRUE CONSTRAINT: Eliminate any answer set with mutex goals
:- goal(X), goal(Y), mutex(X, Y), X != Y.

% This program is UNSATISFIABLE because the constraint rejects any answer set
% where mutex goals coexist (which is always true here!)
