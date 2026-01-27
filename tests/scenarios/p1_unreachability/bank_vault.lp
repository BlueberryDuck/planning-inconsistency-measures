% Scenario 2: Bank Vault
% Thesis Reference: Section 3.2.1
% Expected: I_UR=(1,7), I_MX=(0,0), I_GS=(0,0)
%
% Three parallel chains with missing root preconditions.
% P = {key1, key2, admin_approval, door1_open, door2_open, access_granted, in_vault}
% I = {}
% G = {in_vault}

goal(in_vault).

% open_door1: {key1} -> {door1_open}
% NOTE: key1 is NEVER produced
precond(open_door1, key1).
add(open_door1, door1_open).

% open_door2: {key2} -> {door2_open}
% NOTE: key2 is NEVER produced
precond(open_door2, key2).
add(open_door2, door2_open).

% grant_access: {admin_approval} -> {access_granted}
% NOTE: admin_approval is NEVER produced
precond(grant_access, admin_approval).
add(grant_access, access_granted).

% enter: {door1_open, door2_open, access_granted} -> {in_vault}
precond(enter, door1_open).
precond(enter, door2_open).
precond(enter, access_granted).
add(enter, in_vault).
