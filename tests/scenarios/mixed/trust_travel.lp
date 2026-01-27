% Scenario 5: Trust and Travel
% Thesis Reference: Section 3.2.3
% Expected: I_UR=(0,0), I_MX=(2,1), I_GS=(2,1)
%
% Asymmetric sequencing conflict: opportunity blocks partnership (not vice versa).
% P = {at_local, at_remote, trust, partnership, opportunity}
% I = {at_local, trust}
% G = {partnership, opportunity}

init(at_local).
init(trust).
goal(partnership).
goal(opportunity).

% secure: {at_local, trust} -> {partnership}
precond(secure, at_local).
precond(secure, trust).
add(secure, partnership).

% travel: {at_local} -> {at_remote}, delete {at_local, trust, partnership}
precond(travel, at_local).
add(travel, at_remote).
delete(travel, at_local).
delete(travel, trust).
delete(travel, partnership).

% exploit: {at_remote} -> {opportunity}
precond(exploit, at_remote).
add(exploit, opportunity).

% return: {at_remote} -> {at_local}, delete {at_remote}
precond(return, at_remote).
add(return, at_local).
delete(return, at_remote).
