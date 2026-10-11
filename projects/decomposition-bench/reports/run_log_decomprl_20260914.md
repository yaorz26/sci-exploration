# DecompRL mechanism run log: 2026-09-14

This log records the local, prompt-only mechanism experiment. It is not a claim
of reproducing the paper's 80-H100 training run.

## Fixed rules

- Source: `data/raw/apps_train_introductory50.json`, SHA-256 recorded in the manifest.
- Development: source rows 0--19 (20 problems); holdout: rows 20--49 (30 problems).
- Model for the mechanism comparison: `qwen2.5-coder:7b` via local Ollama.
- Seed: 42; public tests select candidates; private tests are run only after selection.
- Function tasks use the exact starter entrypoint and argument names.
- Per-test timeout: 10 seconds. Executor isolation is a temporary process with `-I`; it is not an OS sandbox.

## Gate and fixture checks

| Check | Result | Interpretation |
| --- | ---: | --- |
| 7B JSON decomposition, 20 tasks | 20/20 valid, entrypoint, DAG | Pass; old v1 record had a validator bug, corrected offline to v2 |
| 7B skeleton decomposition, 20 tasks | 20/20 parse after fence normalization; 0/20 raw-valid | Usable with an explicit normalization flag; raw protocol obedience is poor |
| AST composition fixtures | 3/3 | Pass |
| Leakage tests | pass | Prompts contain no public/private test examples |

The 3B JSON gate was not selected for the development run: 18/20 records were
valid and only 19/20 preserved the exact entrypoint after the contract prompt.

## Three-problem end-to-end smoke

All runs used 3 problems, 4 whole-program candidates for M0/M1, or 2
decompositions x 2 implementations/function and at most 8 combinations for M2.

| Method | Valid generation/implementation | Unique programs evaluated | Selected public full pass | Selected private full pass | Prompt/output tokens | Model seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M0 direct | 12/12 | 12 | 1/3 | 1/3 | 5,880 / 1,831 | 45.147 |
| M1 plan-first | 12/12 | 12 | 1/3 | 1/3 | 6,108 / 3,064 | 69.426 |
| M2a skeleton | 41/44 implementations; 6/6 decompositions | 30 | 0/3 | 1/3 | 32,996 / 5,597 | 177.616 |
| M2b JSON | 36/40 implementations; 6/6 decompositions | 18 | 0/3 | 0/3 | 28,056 / 5,165 | 178.920 |

The smoke confirms the orchestration, public/private isolation, code hashing,
deduplication, and checkpointing. It does not establish a performance winner.
M2a had three rejected nested-function outputs; M2b had one extra top-level
function, three nested-function outputs, and one empty implementation pool.

## First whole-program semantic diagnosis

On `apps-train-2651`, both M0 candidates and both M1 candidates were syntactically
valid but misunderstood the constrained task. They enumerated all representations
of a product as a sum of squares, while the expected answer contains only the
specific identity-derived pairs and canonical ordering. Public pass was 0/5 for
each candidate. This is a real negative example, not an executor failure.

## Development-20 commands

The following runs are checkpointed by problem and can be resumed with the same
command/prefix without `--overwrite`:

```powershell
python scripts/run_whole_program_experiment.py --data data/raw/apps_train_introductory50.json --limit 20 --method direct --model qwen2.5-coder:7b --candidates 4 --timeout 10 --output-prefix data/processed/p3_dev20_m0_direct_qwen25coder_7b_n4_seed42_v1
python scripts/run_whole_program_experiment.py --data data/raw/apps_train_introductory50.json --limit 20 --method plan --model qwen2.5-coder:7b --candidates 4 --timeout 10 --output-prefix data/processed/p3_dev20_m1_plan_qwen25coder_7b_n4_seed42_v1
python scripts/run_modular_smoke.py --data data/raw/apps_train_introductory50.json --limit 20 --protocol skeleton --decomposition-model qwen2.5-coder:7b --implementation-model qwen2.5-coder:7b --decompositions 2 --implementations 2 --max-combinations 8 --timeout 10 --seed 42 --output-prefix data/processed/p3_dev20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1
python scripts/run_modular_smoke.py --data data/raw/apps_train_introductory50.json --limit 20 --protocol json --decomposition-model qwen2.5-coder:7b --implementation-model qwen2.5-coder:7b --decompositions 2 --implementations 2 --max-combinations 8 --timeout 10 --seed 42 --output-prefix data/processed/p3_dev20_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1
```

## Development-20 result

| Method | Candidate coverage | Selected public full pass | Selected private full pass | Private tests passed | Output tokens | Model seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M0 direct | 20/20 | 12/20 | 10/20 | 51/82 | 7,342 | 161.8 |
| M1 plan-first | 20/20 | 14/20 | 13/20 | 58/82 | 14,315 | 307.6 |
| M2a skeleton | 19/20 | 11/20 | 12/20 | 50/79 | 25,825 | 987.6 |
| M2b JSON | 18/20 | 9/20 | 7/20 | 42/75 | 23,769 | 880.8 |

The full-pass denominator is always all 20 development problems; missing
candidates count as unsolved. M2a evaluated 104 unique composed programs and
M2b evaluated 98, compared with 61 for M0 and 63 for M1.

## Current decision

The current mechanism is **No-Go for RL training**. M1 is the strongest method
on this development split (13/20 private full pass). M2a reaches 12/20 and M2b
7/20 despite using far more prompt/output tokens and model time. This decision
applies only to the current introductory split, prompt contract, seed, and
budget. It does not establish that all decomposition methods fail.

The next required evidence is M3 human review on 10 sampled development
problems. The blind review pack contains no public/private execution outcomes.
After the human score and decomposition templates are complete, they will be
validated and the human decompositions will be implemented/evaluated under the
same public-only selection rule.

## M3 human review and execution

The human review was completed on these ten development problems:

`apps-train-2658`, `apps-train-2661`, `apps-train-2657`, `apps-train-2656`,
`apps-train-2652`, `apps-train-2653`, `apps-train-2668`, `apps-train-2671`,
`apps-train-2664`, and `apps-train-2654`.

The review validator accepted 20 blind score rows and 10 human decomposition
rows. After unblinding, the skeleton candidates averaged 7.00/10 and the JSON
candidates averaged 6.50/10 across five criteria: coverage, I/O contract,
dependency clarity, independent implementability, and granularity.

The human decompositions were then evaluated by the same 7B implementation
model, public-only selection, private-after-selection rule, and 10-second
executor timeout. There were 60 implementation requests, 55 valid function
implementations, 60 composable combinations, 26 unique programs evaluated, and
8/10 problems with a candidate. Selected public full pass was 3/10 and selected
private full pass was 3/10 (13/36 private tests, conditional on the eight
covered problems). Five nested-function outputs and two empty implementation
pools were rejected and recorded.

On the same ten questions, the comparable private full-pass counts were M0
3/10, M1 5/10, M2a 6/10, M2b 3/10, and M3 human 3/10. M2a's 6/10 is a small
sample result and does not overturn the full development-20 result, where M1
was 13/20 and M2a was 12/20. The final interpretation remains No-Go for RL:
the current evidence does not show a stable, cost-adjusted, held-out advantage
for automatic decomposition over the plan-first baseline.

Detailed M3 analysis is in `reports/m3_human_analysis_20260914.md`.

## P5 Interview holdout audit (2026-09-17)

The earlier P5 data gate was resolved by fetching 30 APPS train rows with
`difficulty=interview` using `scripts/fetch_apps_subset.py` and recording the
source hash in the manifest. The slice contains 25 callable function tasks and
5 stdin/stdout tasks. Because M2's AST protocol requires a callable starter,
the five stdin/stdout rows were excluded before evaluation; M0/M1 records were
filtered to the same 25 IDs for the paired comparison. This exclusion is a
protocol constraint, not an outcome-based filter.

The executor protocol was strengthened before the formal run: each test has a
10-second limit and each candidate has a 10-second total split budget. A timed
candidate's whole process tree is terminated; unstarted tests remain failures
in the denominator. Selection sees public tests only. Private tests are run
after the selected candidate is frozen, with a separate post-hoc private-pool
audit for oracle/solve@k diagnostics.

Formal commands (all records are checkpointed):

```powershell
python scripts/run_whole_program_experiment.py --data data/raw/apps_train_interview30.json --limit 30 --method direct --model qwen2.5-coder:7b --candidates 2 --timeout 10 --candidate-timeout 10 --output-prefix data/processed/p5_interview30_budget10_m0_direct_qwen25coder_7b_n2_seed42_v2 --overwrite
python scripts/run_whole_program_experiment.py --data data/raw/apps_train_interview30.json --limit 30 --method plan --model qwen2.5-coder:7b --candidates 2 --timeout 10 --candidate-timeout 10 --output-prefix data/processed/p5_interview30_budget10_m1_plan_qwen25coder_7b_n2_seed42_v4 --overwrite
python scripts/run_modular_smoke.py --data data/raw/apps_train_interview_function25.json --limit 25 --protocol skeleton --decomposition-model qwen2.5-coder:7b --implementation-model qwen2.5-coder:7b --decompositions 2 --implementations 2 --max-combinations 8 --timeout 10 --candidate-timeout 10 --seed 42 --output-prefix data/processed/p5_interview_function25_budget10_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1 --overwrite
python scripts/run_modular_smoke.py --data data/raw/apps_train_interview_function25.json --limit 25 --protocol json --decomposition-model qwen2.5-coder:7b --implementation-model qwen2.5-coder:7b --decompositions 2 --implementations 2 --max-combinations 8 --timeout 10 --candidate-timeout 10 --seed 42 --output-prefix data/processed/p5_interview_function25_budget10_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1 --overwrite
```

| Method | Candidate coverage | Selected public full | Selected private full | Selected private tests | Private-pool oracle | Prompt/output tokens | Model seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M0 direct | 25/25 | 11/25 | 9/25 | 54/183 (0.295) | 9/25 | 36,492/11,238 | 380.4 |
| M1 plan-first | 23/25 | 8/25 | 6/25 | 74/178 (0.416) | 8/25 | 37,632/16,569 | 572.8 |
| M2a skeleton | 20/25 | 3/25 | 5/25 | 37/146 (0.253) | 6/25 | 238,358/33,560 | 1,578.4 |
| M2b JSON | 18/25 | 7/25 | 5/25 | 51/150 (0.340) | 5/25 | 266,644/41,248 | 1,389.3 |

On this pre-registered Interview function slice, neither modular method
improves selected private full pass over the direct baseline. M2a and M2b
consume roughly 3--7x the model time and 6--8x the prompt tokens while having
lower candidate coverage. A post-hoc API revalidation removed three M2a and
two M2b decomposition records whose entrypoint argument names did not match
the starter; no model output was regenerated. The private-pool oracle is also
below M0, so the result is not explained only by a weak public selector. Paired bootstrap and
exact sign-test diagnostics are in `reports/p5_interview_function25_analysis_20260917.md`.

The deployment decision remains **No-Go for RL training** under the current
prompt-only mechanism and budget. Keep the P0--P5 artifacts as the baseline;
the next justified experiment is a better decomposition policy or a new
pre-registered slice, not an RL run trained on these noisy modular rewards.
