% STRIPS Planning Problem Representation
% Thesis Reference: Definition 1

% Derive proposition set from problem specification
prop(P) :- init(P).
prop(P) :- add(O, P).
prop(P) :- delete(O, P).
prop(P) :- precond(O, P).
prop(P) :- goal(P).

% Derive operator set
operator(O) :- precond(O, _).
operator(O) :- add(O, _).

% RESULT function: RESULT(s,o) = (s \ delete(o)) U add(o)
result_holds(P, S, O) :- state(S), applicable(O, S), holds(P, S), not delete(O, P).
result_holds(P, S, O) :- state(S), applicable(O, S), add(O, P).
