% Unsatisfiable Scenario (Edge Case)
%
% Tests that the system raises an error when the ASP program is
% unsatisfiable. The integrity constraint rejects all answer sets.
%
% Expected: RuntimeError

init(a).
goal(a).

precond(noop, a).
add(noop, a).

:- #true.
