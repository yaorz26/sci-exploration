# DecompRL mechanism ablation: development-20

This report compares prompt-only mechanisms on the frozen custom APPS train split. It is a local mechanism smoke, not a paper-scale DecompRL reproduction.

## Fairness rules

All runs use Qwen2.5-Coder 7B through local Ollama, seed 42, exact starter APIs, 10-second per-test timeout, public-only candidate selection, and private evaluation only after the selection record is frozen. M0/M1 use four whole-program candidates per problem. M2a/M2b use two decompositions, two implementations per function, and at most eight combinations per decomposition. Duplicate code hashes are executed once and counted separately.

## Results

| Method | Valid outputs | Candidate coverage | Unique programs executed | Selected public full | Selected private full | Selected private test rate | Prompt/output tokens | Model seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M0 | 80/80 | 20/20 | 61 | 12/20 | 10/20 | 0.622 (51/82) | 29060/7342 | 161.8 |
| M1 | 80/80 | 20/20 | 63 | 14/20 | 13/20 | 0.707 (58/82) | 30580/14315 | 307.6 |
| M2a | decomp 40/40; impl 248/262 | 19/20 | 104 | 11/20 | 12/20 | 0.633 (50/79) | 166158/25825 | 987.6 |
| M2b | decomp 39/40; impl 235/254 | 18/20 | 98 | 9/20 | 7/20 | 0.560 (42/75) | 143218/23769 | 880.8 |

The full-pass columns use all 20 problems as the denominator; a problem without a valid candidate is counted as not solved. Candidate coverage is shown separately. The test-rate column is more granular because APPS problems have different numbers of private examples.

## Interpretation

M1 improves selected full private passes over M0 on this development slice, but uses almost twice the output tokens and model time. Neither modular protocol beats M1 at this budget: M2a and M2b have lower selected private full-pass counts and much higher generation/combination cost. This is a No-Go for RL training under the current prompt-only mechanism and budget; it is not evidence that decomposition can never help on harder data or with a better policy.

M2a produced 14 rejected nested-function implementations. M2b produced rejected extra/nested functions, one forward dependency, one unknown dependency, and empty implementation pools. These failures are reported as contract failures rather than silently repaired.

## Reproducibility

The raw JSONL records and summaries are under `data/processed/`. Each run is checkpointed by problem; rerunning the same command and prefix resumes unfinished problems. The executor uses an isolated temporary Python process but is not an OS sandbox, so this local experiment must not execute untrusted arbitrary code.
