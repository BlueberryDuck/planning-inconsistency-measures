% Scenario 6: Rival Alliances
% Expected: I_UR=(0,0), I_MX=(2,1), I_GS=(2,2)
%
% Symmetric sequencing conflict: each alliance blocks the other.
% P = {neutral_A, neutral_B, allied_A, allied_B}
% I = {neutral_A, neutral_B}
% G = {allied_A, allied_B}

init(neutral_A).
init(neutral_B).
goal(allied_A).
goal(allied_B).

% ally_A: {neutral_A} -> {allied_A}, delete {neutral_B}
precond(ally_A, neutral_A).
add(ally_A, allied_A).
delete(ally_A, neutral_B).

% ally_B: {neutral_B} -> {allied_B}, delete {neutral_A}
precond(ally_B, neutral_B).
add(ally_B, allied_B).
delete(ally_B, neutral_A).
