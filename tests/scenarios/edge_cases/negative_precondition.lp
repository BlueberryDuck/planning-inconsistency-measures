% Negative Precondition Scenario (Edge Case)
%
% Tests that neg_precond correctly blocks operator application.
% Two goals: a (in init) and b. Operator o1 adds b but has
% neg_precond on a — it can only fire when a is false. Since a
% is always true (nothing deletes it), o1 is never applicable,
% so b is unreachable.
%
% Expected: (1, 1, 0, 0, 0, 0) — b unreachable

init(a).
goal(a).
goal(b).

% o1: adds b, but only when a is false
precond(o1, c).
add(o1, c).
neg_precond(o1, a).
add(o1, b).

% Ensure c exists so o1 has a precondition
init(c).
