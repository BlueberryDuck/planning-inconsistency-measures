% Bridge: plasp output format → internal measure computation format
%
% Maps plasp's PDDL-to-ASP vocabulary to the simpler predicates
% expected by planning.lp and reachability.lp. In ASP, goal/1 and
% goal/2 are distinct predicates, so the derivation is clean.
%
% plasp predicates used:
%   initialState(Variable, Value)
%   goal(Variable, Value)              [arity 2, distinct from our goal/1]
%   action(Action)
%   variable(Variable)
%   precondition(Action, Variable, Value)
%   postcondition(Action, Effect, Variable, Value)
%
% Our internal predicates derived:
%   init/1, goal/1, precond/2, neg_precond/2, add/2, delete/2

init(V) :- initialState(V, value(V, true)).
goal(V) :- goal(V, value(V, true)).

precond(A, V) :- precondition(A, V, value(V, true)).
neg_precond(A, V) :- precondition(A, V, value(V, false)).

add(A, V) :- postcondition(A, effect(unconditional), V, value(V, true)).
delete(A, V) :- postcondition(A, effect(unconditional), V, value(V, false)).
