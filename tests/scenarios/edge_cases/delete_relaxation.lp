% Delete-Relaxation Divergence Test
%
% This scenario tests that reachability accounts for delete effects.
% Under delete-relaxed reachability, c is reachable (a reachable via
% init, b reachable via o1, so o2 fires). But in the real state space:
%   {a} -> apply o1 -> {b}
% The states {a} and {b} are the only reachable states; {a,b} never
% coexists, so o2 is never applicable and c is never truly reachable.
%
% Expected: I_UR = (1, 1, 0, 0, 0, 0)
%   - c is the only goal and it is unreachable
%   - c is the only unreachable proposition (a, b are both reachable)

init(a).
goal(c).

% o1: {a} -> add {b}, delete {a}
precond(o1, a).
add(o1, b).
delete(o1, a).

% o2: {a, b} -> add {c}
precond(o2, a).
precond(o2, b).
add(o2, c).
