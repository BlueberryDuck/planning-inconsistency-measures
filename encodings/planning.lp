% STRIPS Planning Problem Representation
%
% Derives proposition and operator sets from problem facts.
% Input predicates: init/1, goal/1, precond/2, add/2, delete/2

% ============================================================
% Derived Sets
% ============================================================

% Derive proposition set from problem specification
prop(P) :- init(P).
prop(P) :- add(_, P).
prop(P) :- delete(_, P).
prop(P) :- precond(_, P).
prop(P) :- goal(P).

% Derive operator set
operator(O) :- precond(O, _).
operator(O) :- add(O, _).

% ============================================================
% Output
% ============================================================
#show goal/1.
