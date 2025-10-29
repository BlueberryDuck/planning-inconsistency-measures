% 1. Add facts for a 4-block tower: d on c on b on a on table
block(a).
block(b).
block(c).
block(d).
on(d, c).
on(c, b).
on(b, a).
on(a, table).

%    Then use rules to derive which blocks are above which.
above(X, Y) :- on(X, Y), block(X), block(Y).
above(X, Y) :- on(X, Z), above(Z, Y), block(X), block(Z), block(Y).

% 2. Add a constraint that prevents blocks from being on themselves (cycle).
:- above(X, Y), above (Y, X).
:- on(X, X).

% 4. Try adding contradictory facts and see what happens:
%    clear(a). has_block_on_top(a).
has_block_on_top(X) :- on(Y, X), block(Y).
clear(X) :- block(X), not has_block_on_top(X).
:- has_block_on_top(X), clear(X).

has_block_on_top(a).
clear(a).
