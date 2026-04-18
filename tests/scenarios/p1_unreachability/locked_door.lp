% Scenario 1: Locked Door
% Expected: I_UR=(1,3), I_MX=(0,0), I_GS=(0,0)
%
% Linear dependency chain where root (has_key) is never produced.
% P = {at_door, has_key, door_unlocked, in_room}
% I = {at_door}
% G = {in_room}

init(at_door).
goal(in_room).

% unlock: {at_door, has_key} -> {door_unlocked}
% NOTE: has_key is NEVER produced - this is the unsolvability source
precond(unlock, at_door).
precond(unlock, has_key).
add(unlock, door_unlocked).

% enter: {at_door, door_unlocked} -> {in_room}, deletes at_door
precond(enter, at_door).
precond(enter, door_unlocked).
add(enter, in_room).
delete(enter, at_door).
