% ==============================================================================
% EXAMPLE 3: Choice Rules - Non-deterministic Selection
% ==============================================================================
% Choice rules generate MULTIPLE answer sets (solutions)
% Run this: clingo example3_choice.lp 0
%          (the 0 means "show all answer sets")
% ==============================================================================

% Facts: We have 3 nodes in a graph
node(1).
node(2).
node(3).

% Facts: Edges between nodes
edge(1, 2).
edge(2, 3).
edge(1, 3).

% Choice rule: Each node gets EXACTLY one color (red, blue, or green)
1 {color(X, red); color(X, blue); color(X, green)} 1 :- node(X).

% Constraint: Adjacent nodes must have different colors
:- edge(X, Y), color(X, C), color(Y, C).

% Show the coloring
#show color/2.

% ==============================================================================
% WHAT YOU'LL SEE:
% - Multiple answer sets (different valid colorings)
% - Each respects the constraint (no adjacent nodes have same color)
%
% RELEVANCE TO YOUR THESIS:
% - Choice rules can help explore different "conflict sets"
% - Constraints eliminate invalid configurations
% - This is the foundation for finding MINIMAL inconsistent subsets!
% ==============================================================================
