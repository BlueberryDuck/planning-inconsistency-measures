% ==============================================================================
% EXAMPLE 1: Facts and Rules - Your First ASP Program
% ==============================================================================
% Run this: clingo example1_facts_rules.lp
% ==============================================================================

% Facts: A simple blocks world
on(a, table).
on(b, a).
on(c, table).

block(a).
block(b).
block(c).

% Rule: X is clear if no block is on top of X
clear(X) :- block(X), not has_block_on_top(X).

% Rule: X has a block on top if some Y is on X
has_block_on_top(X) :- on(Y, X), Y != table.

% Rule: X is above Z if X is directly on Z
above(X, Z) :- on(X, Z), Z != table.

% Rule: X is above Z if X is on Y, and Y is above Z (transitivity)
above(X, Z) :- on(X, Y), above(Y, Z).

% Tell clingo what to show in the output
#show on/2.
#show clear/1.
#show above/2.
