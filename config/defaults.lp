% ============================================================
% Default Configuration for Thesis Measure Computation
% ============================================================
%
% This file defines default constants used across the encodings.
% Values can be overridden via the clingo command line.
%
% Example: clingo encodings/planning.lp encodings/reachability.lp \
%                 encodings/measures/*.lp problem.lp -c horizon=100
%
% ============================================================

% ------------------------------------------------------------
% Horizon: Maximum steps for state-space exploration
% ------------------------------------------------------------
% Controls how deep the bounded search explores execution paths.
%
% Effects:
%   - Higher values find more reachable states (fewer false positives)
%   - Lower values run faster but may miss long plans
%
% Guidelines:
%   - Default (20): Sufficient for most small/medium problems
%   - IPC benchmarks: May need 50-100 depending on domain
%   - Use tools/horizon_analysis.sh to determine optimal value
%
% If solvable instances show non-zero measures, increase horizon.

#const horizon = 20.
