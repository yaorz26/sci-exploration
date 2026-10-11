# CodePRM Reproduction (minimal, reproducible baseline)

This directory implements the current milestone from `CodePRM_完整复现规划.md`:

1. inspect the runtime;
2. execute candidate programs against public/private tests with a timeout;
3. generate four deterministic offline candidates for 20 APPS-Intro-like tasks;
4. compare first, random, public-pass-rate, and private-test oracle selection.

The offline dataset is deliberately small and self-contained. It validates the data
flow and metrics without claiming to reproduce the paper's model numbers. A real
APPS export can be supplied as JSON/JSONL through `--apps-path`; see
`src/data_loader.py` for the accepted fields.

The next executable route, including task order, acceptance gates, feasibility
limits, expected outputs, and the boundary of what can be claimed, is documented
in [`docs/plans/执行计划_当前可行路线.md`](docs/plans/执行计划_当前可行路线.md).

## Run

```powershell
cd codeprm-reproduction
python scripts/check_environment.py
python scripts/prepare_offline_data.py
python scripts/run_one_problem.py --problem-id offline-001
python scripts/run_baseline.py --config configs/minimal.yaml
python scripts/run_level2.py
python scripts/run_gvr.py
python scripts/run_mcts.py
```

Results are written to `outputs/executions/` and `outputs/results/`; the summary
table is also copied to `reports/tables/baseline.csv`.

## Local Ollama generation

The project can use a locally running Ollama server instead of the deterministic
offline generator. `qwen2.5-coder:1.5b` is the fast code-generation baseline;
`qwen2.5-coder:3b` is the recommended local option. Both run within the RTX
4060 Laptop GPU's 8 GB memory budget.

```powershell
ollama pull qwen2.5-coder:3b
python scripts/run_one_problem.py --generator-backend ollama --generator-model qwen2.5-coder:3b
python scripts/run_baseline.py --config configs/ollama.yaml --output-suffix ollama_qwen25coder_3b
```

The shown model pull is already complete in this workspace. Local-model
outputs retain their raw response, parsed thoughts, generated code, execution
feedback, seed, and model name. They are saved with a model-specific suffix so
they never overwrite offline-fixture results.

## Real APPS subset

The first real subset is already fetched and pinned from the Hugging Face
`codeparrot/apps` revision recorded in
`data/splits/apps_train_introductory20.json`. It contains 20 Introductory
function-style tasks from the `train` split. The project detects the function
signature in `starter_code`, invokes it through an isolated harness, and keeps
the original `solutions` field out of the normalized file.

To reproduce the fetch in the dedicated Python 3.12 environment:

```powershell
py -3.12 -m venv .venv_apps
\.venv_apps\Scripts\python.exe -m pip install "datasets==2.21.0" requests
\.venv_apps\Scripts\python.exe scripts\fetch_apps_subset.py `
  --split train --difficulty introductory --limit 20 `
  --output data\raw\apps_train_introductory20.json `
  --manifest data\splits\apps_train_introductory20.json
```

Run one real local-model smoke test:

```powershell
python scripts\run_one_problem.py `
  --apps-path data\raw\apps_train_introductory20.json `
  --problem-id apps-train-2651 `
  --generator-backend ollama `
  --generator-model qwen2.5-coder:3b `
  --num-candidates 1
```

The split uses the first half of each APPS `input_output` example list as
public and the remainder as private. This is an explicit custom evaluation
policy, not the paper's official private split; use the official test split for
strict benchmark comparisons when bandwidth permits.

## Reproduce the completed real-data run

The following commands reuse the fixed candidate pool where possible, so the
Level-2, GVR, and MCTS comparisons do not spend additional Ollama calls:

```powershell
python scripts\run_baseline.py `
  --config configs\apps_train_ollama_qwen25coder_3b.yaml `
  --apps-path data\raw\apps_train_introductory20.json `
  --output-suffix apps_train_intro20_qwen3b

python scripts\run_level2.py `
  --apps-path data\raw\apps_train_introductory20.json `
  --feedback-path data\processed\feedback_records_apps_train_intro20_qwen3b.jsonl `
  --output-suffix apps_train_intro20_qwen3b

python scripts\run_gvr.py `
  --apps-path data\raw\apps_train_introductory20.json `
  --feedback-path data\processed\feedback_records_apps_train_intro20_qwen3b.jsonl `
  --output-suffix apps_train_intro20_qwen3b

python scripts\run_mcts.py `
  --apps-path data\raw\apps_train_introductory20.json `
  --feedback-path data\processed\feedback_records_apps_train_intro20_qwen3b.jsonl `
  --output-suffix apps_train_intro20_qwen3b --rollouts 8

python scripts\run_model_gvr.py `
  --apps-path data\raw\apps_train_introductory20.json `
  --feedback-path data\processed\feedback_records_apps_train_intro20_qwen3b.jsonl `
  --generator-model qwen2.5-coder:3b `
  --output-suffix apps_train_intro20_qwen3b
```

The corresponding result files are under `outputs/results/`, tables under
`reports/tables/`, and the interpretation is recorded in
`reports/experiment_log.md`.

The detailed next-stage research plan is in
`docs/plans/下一阶段研究计划_神经CodePRM与结构化扩展.md`. It includes the WSL neural
CodePRM pilot, step-level labels, GVR error analysis, structured function/AST
features, official-split validation, and explicit feasibility gates.

The WSL 3B QLoRA environment and two-step training smoke are complete. The
smoke uses explicitly marked proxy step labels; see
`reports/t02_t03_pilot_smoke_2026-09-05.json` before interpreting any neural
PRM metric.

The continuation-level train-20 pilot now has three seeds (236/240/240 exact
continuation records). With a sigmoid-calibrated head and pooled training, the
neural selector averages `0.456 +/- 0.069` private pass rate on the three seed
candidate pools, versus `0.400 +/- 0.067` for the first candidate and `0.633`
for direct public selection. This is still an exploratory feasibility result:
the end-to-end QLoRA path works, but the current scorer has not surpassed the
execution-feedback selector and structured feature ablations remain deferred
until larger training data are available.

The first strict train-50 neural diagnostic is also complete for seed 42:
1,196 continuation records over 598 nodes, with a problem-level 37/13 split.
Soft labels, binary BCE, and deployment-aligned inputs all remained below the
first candidate (`0.533`) and direct public selection (`0.683`) on private pass
rate. The configuration is therefore paused before expensive seed43/44 data
collection; see `reports/neural_codeprm_train50_seed42_diagnostic_2026-09-05.json`.

## Completed train-50 experiment

The fixed 50-problem subset is stored at
`data/raw/apps_train_introductory50.json`. All three baseline seeds, the Ridge
ablation, pool-replacement GVR, simplified MCTS, and model-backed GVR are
complete. The three-seed baseline result is public selection `0.572±0.032`
private pass rate versus first candidate `0.445±0.028`; the full interpretation
is in `reports/experiment_log.md`.

```powershell
python scripts\aggregate_baseline_seeds.py `
  --results outputs\results\baseline_apps_train_intro50_qwen3b_seed42.json `
            outputs\results\baseline_apps_train_intro50_qwen3b_seed43.json `
            outputs\results\baseline_apps_train_intro50_qwen3b_seed44.json `
  --output-suffix apps_train_intro50_qwen3b_seeds
```

The fixed input contains 50 problems, 220 public tests, and 246 private tests.
These results use the documented custom train-split public/private policy and
are still a reduced-scale reproduction.

## Reproducibility

All experiment parameters live in YAML-like JSON-compatible config files. The
minimal runner uses seed 42, four candidates per problem, and a two-second
per-test timeout. For strict APPS reproduction, record the dataset version,
public/private split, generator model, and API settings in the resulting report.

## Safety boundary

The executor runs untrusted candidate code in a temporary working directory and
enforces a process timeout. This is a development executor, not a security
sandbox: do not run hostile code on a production machine. A container or OS-level
sandbox is required for adversarial workloads.
