% ==============================================================================
% EXAMPLE 2: Constraints - Detecting Conflicts
% ==============================================================================
% This demonstrates conflict detection, central to your thesis work!
% Run this: clingo example2_constraints.lp
% ==============================================================================

% Facts: Planning goals
goal(robot_at_a).
goal(robot_at_b).
goal(door_open).
goal(door_closed).

% Facts: Mutual exclusions (from domain knowledge)
mutex(robot_at_a, robot_at_b).  % Robot can't be in two places
mutex(robot_at_b, robot_at_a).
mutex(door_open, door_closed).  % Door can't be both open and closed
mutex(door_closed, door_open).

% Constraint: Flag a conflict if two mutex goals exist
conflict(X, Y) :- goal(X), goal(Y), mutex(X, Y), X != Y.

% Show the conflicts
#show conflict/2.

% ==============================================================================
% TRY THIS:
% 1. Comment out one of the mutex goals (e.g., goal(door_closed))
% 2. Run again - you should see fewer conflicts
% 3. This is how you'll detect Type 1 unsolvability (Goal Mutex) in planning!
% ==============================================================================
