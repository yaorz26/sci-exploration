# P5 Interview function25 mechanism comparison

This is the frozen P5 comparison on the 25 function-style rows from the 30-row Interview slice. The five stdin/stdout rows are excluded from every method in this table because the modular protocol requires a callable starter API.

All formal runs use Qwen2.5-Coder 7B through Ollama, seed 42, public-only selection, 10s per test, and 10s total candidate budget per split. Private tests are never used for selection.

## Results

| Method | Rows with candidate | Selected public full | Selected private full | Private selected tests | Public tie rate | Calls | Model seconds | Prompt/output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M0 | 25/25 | 11/25 | 9/25 | 54/183 (0.295) | 17/25 (0.680) | 60 | 380.4 | 36492/11238 |
| M1 | 23/25 | 8/25 | 6/25 | 74/178 (0.416) | 16/23 (0.696) | 60 | 572.8 | 37632/16569 |
| M2a | 20/25 | 3/25 | 5/25 | 37/146 (0.253) | 20/20 (1.000) | 308 | 1578.4 | 238358/33560 |
| M2b | 18/25 | 7/25 | 5/25 | 51/150 (0.340) | 16/18 (0.889) | 354 | 1389.3 | 266644/41248 |

`selected private full` is the deployable pass@1-style metric: choose the highest public pass-rate candidate, then test that one privately. `public tie rate` is the fraction of covered rows with at least two candidates tied at the best public rate; the registered index tie-break resolves those ties. `oracle` is the number of rows with at least one private-passing candidate in the frozen generated pool; it is diagnostic and is not a deployable selection result.

## Solve@k

The runs generated two whole-program candidates for M0/M1 and at most sixteen composed candidates for M2a/M2b. Therefore solve@8 is estimable only for M2a/M2b, while solve@32 and solve@64 are not identifiable from this budget and are reported as N/A rather than extrapolated.

| Method | pool solve@1 | solve@8 | solve@32 | solve@64 | private pool oracle |
| --- | ---: | ---: | ---: | ---: | ---: |
| M0 | 9/25 | N/A | N/A | N/A | 9/25 |
| M1 | 4/25 | N/A | N/A | N/A | 8/25 |
| M2a | 4/25 | 6/25 | N/A | N/A | 6/25 |
| M2b | 4/25 | 5/25 | N/A | N/A | 5/25 |

## Paired differences

| Pair | Selected-private full difference | Bootstrap 95% CI | Exact paired sign p |
| --- | ---: | ---: | ---: |
| M1 - M0 | -5/25 | [-0.400, +0.000] | 0.1250 |
| M2a - M1 | +0/25 | [-0.160, +0.160] | 1.0000 |
| M2b - M1 | +0/25 | [-0.200, +0.200] | 1.0000 |

## Execution accounting

Candidate timeout exhaustion is counted as failure with the denominator preserved. The executor terminates the complete process tree on timeout, so a child process cannot keep a run alive or consume an unbounded hidden budget.

| Method | Candidate budget exhausted (selected private) | Public candidate-test total | Unique programs | Invalid/contract errors |
| --- | ---: | ---: | ---: | ---: |
| M0 | 4 | 334 | 46 | 2 |
| M1 | 1 | 330 | 44 | 4 |
| M2a | 1 | 1708 | 117 | 34 |
| M2b | 3 | 1396 | 127 | 53 |

## Decision

Use selected private full as the primary deployment metric. Use oracle and solve@k only to distinguish search-space coverage from selection quality. If modular methods do not improve selected private performance while materially increasing model calls/tokens, do not start RL training on this setup; retain the frozen data, prompts, and executor as a reproducible baseline and revisit only with a better decomposition policy or a harder, pre-registered slice.

Raw records remain under `data/processed/` and contain the public selection record plus the post-selection private result.

## Failure boundaries

`no candidate` is a protocol/generation failure. `selector missed` means the frozen pool contained a private-passing candidate but public selection chose another. `pool no solution` means no generated candidate passed all private tests, so selection could not have recovered it.

| Method | No candidate | Selector missed | Pool no private solution |
| --- | ---: | ---: | ---: |
| M0 | 0 | 0 | 16 |
| M1 | 2 | 2 | 15 |
| M2a | 5 | 1 | 14 |
| M2b | 7 | 0 | 13 |
