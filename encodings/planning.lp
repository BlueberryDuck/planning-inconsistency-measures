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
