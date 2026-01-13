% Scenario 1: Locked Door
% Thesis Reference: Section 3.2.1
% Expected: I_UR=(1,3), I_MX=(0,0), I_GS=(0,0)
%
% Linear dependency chain where root (has_key) is never produced.
% P = {has_key, door_unlocked, in_room}
% I = {}
% G = {in_room}

goal(in_room).

% unlock: {has_key} -> {door_unlocked}
% NOTE: has_key is NEVER produced - this is the unsolvability source
precond(unlock, has_key).
add(unlock, door_unlocked).

% enter: {door_unlocked} -> {in_room}
precond(enter, door_unlocked).
add(enter, in_room).
