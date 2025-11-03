% ==============================================================================
% ASP TUTORIAL 1: BASIC SYNTAX
% ==============================================================================
% This tutorial covers the fundamental building blocks of Answer Set Programming
% that you'll need for implementing your planning inconsistency measures.
%
% HOW TO USE:
%   Run sections individually by copying them to separate files, or
%   comment/uncomment sections to test specific concepts.
%
%   To run: clingo 01_basics.lp
% ==============================================================================


% ==============================================================================
% SECTION 1: FACTS
% ==============================================================================
% Facts are unconditionally true statements. They form the "database" of your
% problem. In planning, these might represent initial state propositions.

% Example: A simple blocks world scenario
% Uncomment to test:
% on(a, table).
% on(b, a).
% on(c, table).
% block(a).
% block(b).
% block(c).
% clear(b).
% clear(c).


% ==============================================================================
% SECTION 2: RULES
% ==============================================================================
% Rules have the form: head :- body.
% Meaning: "head is true IF body is true"
%
% Variables start with UPPERCASE, predicates with lowercase.

% Example: Define when a block is stackable
% stackable(X) :- block(X), clear(X).

% Example: Transitivity - useful for reachability analysis in planning
% above(X, Z) :- on(X, Z).
% above(X, Z) :- on(X, Y), above(Y, Z).


% ==============================================================================
% SECTION 3: NEGATION (not)
% ==============================================================================
% "not" means "negation as failure" - true if cannot be proven true
% This is CRUCIAL for your work, as it relates to paraconsistent semantics!

% Example: A block has nothing on it if we can't prove something is on it
% clear(X) :- block(X), not has_block_on_top(X).
% has_block_on_top(X) :- on(Y, X).


% ==============================================================================
% SECTION 4: CONSTRAINTS
% ==============================================================================
% Constraints eliminate answer sets. Format: :- body.
% Meaning: "It must NOT be the case that body is true"
%
% This is key for detecting conflicts in planning problems!

% Example: No block can be both clear and have something on it
% :- clear(X), has_block_on_top(X).

% Example: Goal mutex - can't achieve two mutually exclusive goals
% :- goal(on(a, b)), goal(on(b, a)).


% ==============================================================================
% SECTION 5: CHOICE RULES
% ==============================================================================
% Choice rules generate multiple answer sets (non-determinism).
% Format: {atom1; atom2; ...} :- body.
% Meaning: "Choose any subset of these atoms if body is true"

% Example: Choose which blocks to move
% {move(X)} :- block(X), clear(X).

% You can add bounds:
% 1 {color(X, red); color(X, blue); color(X, green)} 1 :- node(X).
% Meaning: Choose EXACTLY 1 color for each node


% ==============================================================================
% PRACTICAL EXAMPLE: GOAL MUTEX DETECTION
% ==============================================================================
% This example demonstrates detecting mutually exclusive goals in planning.
% This is directly relevant to your Type 1 unsolvability (Goal Mutex).

% Facts: Define some goal propositions
goal_prop(at_location_a).
goal_prop(at_location_b).
goal_prop(door_open).
goal_prop(door_closed).

% Facts: Which goals are in the goal set
in_goal(at_location_a).
in_goal(door_closed).

% Rule: Two goals are mutex if they can't both be true
mutex(X, Y) :- goal_prop(X), goal_prop(Y), X != Y, contradicts(X, Y).

% Facts: Define contradictions (domain knowledge)
contradicts(door_open, door_closed).
contradicts(door_closed, door_open).

% Constraint: Detect if we have mutex goals in the goal set
goal_conflict :- in_goal(X), in_goal(Y), mutex(X, Y).

% Show what we found
#show goal_conflict/0.
#show mutex/2.


% ==============================================================================
% EXERCISES FOR YOU
% ==============================================================================
% Try these to test your understanding:
%
% 1. Add facts for a 4-block tower: d on c on b on a on table
%    Then use rules to derive which blocks are above which.
%
% 2. Add a constraint that prevents blocks from being on themselves (cycle).
%
% 3. Define a rule that detects unreachable propositions:
%    A proposition is unreachable if no action can make it true.
%    (This relates to your Type 2 unsolvability!)
%
% 4. Try adding contradictory facts and see what happens:
%    clear(a). has_block_on_top(a).
%    Does clingo find an answer set? Why or why not?


% ==============================================================================
% KEY CONCEPTS FOR YOUR THESIS
% ==============================================================================
% 1. CONSTRAINTS detect conflicts - central to inconsistency measurement!
% 2. NEGATION (not) relates to your paraconsistent "neither true nor false"
% 3. CHOICE RULES will be useful for exploring different conflict sets
% 4. RULES propagate information - like state transitions in planning
%
% Next: Study how plasp translates PDDL actions into ASP rules with time steps!
% ==============================================================================
