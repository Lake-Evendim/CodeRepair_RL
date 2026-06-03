# MiniRepair-RL

RL for Test-Verifiable Code Repair Agents. A complete pipeline that trains code repair agents using SFT and REINFORCE-based RL, with execution-based rewards and anti-reward-hacking guardrails.

## Architecture

```
                    ┌─────────────┐
                    │  Benchmark  │
                    │ 130 tasks   │
                    │ 2 repos     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Agent     │
                    │ ReAct/SFT/RL│
                    └──────┬──────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    CodeRepairEnv       │
              │ MDP: 6 steps, 2 edits  │
              └───────────┬────────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ read_file  │ │ edit_file  │ │ run_tests  │
    │ search_code│ │ guardrails │ │   submit   │
    └────────────┘ └────────────┘ └────────────┘

    ┌──────────┐   ┌───────────┐   ┌───────────┐
    │ SFT LoRA │──▶│ REINFORCE │──▶│ Eval &    │
    │ TRL      │   │ sparse/   │   │ Reports   │
    │          │   │ dense     │   │           │
    └──────────┘   └───────────┘   └───────────┘
```

## Key Results

| Method | Test Hidden Pass | Public Pass | Invalid Edit | Avg Steps | Avg Regressions |
|--------|:----------------:|:-----------:|:------------:|:---------:|:---------------:|
| ReAct (base) | 60.0% | 3.3% | 0.13 | 5.53 | 0.20 |
| SFT (LoRA) | **70.0%** | 16.7% | 0.60 | 4.47 | 0.10 |
| RL Sparse | **70.0%** | 16.7% | 0.57 | 4.47 | 0.10 |
| RL Dense | **70.0%** | 16.7% | 0.60 | 4.40 | 0.07 |

Base model: Qwen2.5-Coder-1.5B-Instruct. Hardware: RTX 4090 24GB.

SFT and RL both achieve 70% hidden pass rate (+10% over ReAct). RL Dense slightly reduces regressions (0.07 vs 0.10) and avg steps (4.40 vs 4.47) compared to SFT, but hidden pass rate does not improve further. The benchmark may be too simple for RL to show clear benefit over SFT.

## Installation

```bash
pip install -e '.[dev]'
# With training dependencies (transformers, peft, trl):
pip install -e '.[dev,train]'
```

## Quick Start

### 1. Generate Benchmark

```bash
python scripts/generate_tasks.py --seed 42 --output benchmarks
python scripts/validate_tasks.py --tasks benchmarks/train benchmarks/validation benchmarks/test
```

Produces 130 tasks: 80 train, 20 validation, 30 test. Each task has public tests (agent-visible), private tests (reward signal), and hidden tests (test split only, final evaluation).

### 2. Run ReAct Baseline

```bash
python scripts/evaluate.py \
  --method react \
  --split validation \
  --eval-mode validation_selection \
  --policy qwen_base \
  --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --output logs/eval/react_validation

python scripts/evaluate.py \
  --method react \
  --split test \
  --eval-mode final_test \
  --policy qwen_base \
  --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --output logs/eval/react_test
```

### 3. Build SFT Dataset

```bash
python scripts/build_sft_dataset.py \
  --benchmark-root benchmarks \
  --source-split train \
  --dev-fraction 0.1 \
  --seed 42 \
  --output-train data/sft_train.jsonl \
  --output-dev data/sft_dev.jsonl
```

SFT targets are constructed from train split gold patches only. Validation/test splits are never used for SFT data.

### 4. Train SFT

```bash
python scripts/train_sft.py --config configs/sft.yaml
# Dry-run (8 samples, 2 steps):
python scripts/train_sft.py --config configs/sft.yaml --dry-run
```

### 5. Train RL (Sparse / Dense)

```bash
python scripts/train_rl_sparse.py --config configs/rl_sparse.yaml
python scripts/train_rl_dense.py --config configs/rl_dense.yaml
# Dry-run (2 tasks, 1 update):
python scripts/train_rl_sparse.py --config configs/rl_sparse.yaml --dry-run
```

RL starts from the SFT adapter and uses REINFORCE with moving-average baseline.

### 6. Evaluate All Methods

```bash
# SFT
python scripts/evaluate.py --method sft --split validation --eval-mode validation_selection --adapter outputs/sft_adapter_trained --output logs/eval/sft_validation
python scripts/evaluate.py --method sft --split test --eval-mode final_test --adapter outputs/sft_adapter_trained --output logs/eval/sft_test

# RL Sparse
python scripts/evaluate.py --method rl_sparse --split validation --eval-mode validation_selection --adapter outputs/rl_sparse_adapter_trained --output logs/eval/rl_sparse_validation
python scripts/evaluate.py --method rl_sparse --split test --eval-mode final_test --adapter outputs/rl_sparse_adapter_trained --output logs/eval/rl_sparse_test

# RL Dense
python scripts/evaluate.py --method rl_dense --split validation --eval-mode validation_selection --adapter outputs/rl_dense_adapter_trained --output logs/eval/rl_dense_validation
python scripts/evaluate.py --method rl_dense --split test --eval-mode final_test --adapter outputs/rl_dense_adapter_trained --output logs/eval/rl_dense_test
```

### 7. Generate Reports

```bash
# Main results
python scripts/summarize_metrics.py \
  --inputs logs/eval/react_test logs/eval/sft_test logs/eval/rl_sparse_test logs/eval/rl_dense_test \
  --require-main-comparable \
  --output reports/main_results.md

# Reward ablation
python scripts/compare_rewards.py \
  --validation-inputs logs/eval/rl_sparse_validation logs/eval/rl_dense_validation \
  --test-inputs logs/eval/rl_sparse_test logs/eval/rl_dense_test \
  --output reports/reward_ablation.md

# Failure analysis
python scripts/analyze_failures.py \
  --inputs logs/eval/react_validation logs/eval/react_test \
           logs/eval/sft_validation logs/eval/sft_test \
           logs/eval/rl_sparse_validation logs/eval/rl_sparse_test \
           logs/eval/rl_dense_validation logs/eval/rl_dense_test \
  --output reports/failure_analysis.md
```

Note: The actual evaluation logs in this repo use suffixed directory names (e.g. `react_test_full`, `rl_sparse_test_trained`). Adjust the `--inputs` paths accordingly when reproducing.

## Project Structure

```
minirepair/
  env/          # CodeRepairEnv, tools, sandbox, guardrails, reward
  data/         # Task schema, bug catalog, generator, SFT builder
  agents/       # ReAct agent, SFT/RL policy backends, action parser
  training/     # SFT (LoRA), REINFORCE RL, rollout, log-prob
  evaluation/   # Evaluator, metrics, failure taxonomy, reports
configs/        # sft.yaml, rl_sparse.yaml, rl_dense.yaml
scripts/        # CLI entry points (21 scripts)
benchmarks/     # train/ (80), validation/ (20), test/ (30)
tests/          # 19 test files
reports/        # Generated reports
logs/           # Evaluation logs and trajectories
```

## Failure Analysis Summary

Top failure categories across all methods (177 failed episodes):

| Category | Count | % |
|----------|:-----:|:--:|
| Invalid edit (guardrail blocked) | 90 | 50.8% |
| Regression error | 31 | 17.5% |
| Tool misuse (no edit attempted) | 27 | 15.3% |
| Invalid action (bad JSON) | 13 | 7.3% |
| Localization error | 10 | 5.6% |
| Premature submit | 6 | 3.4% |

## Limitations

1. **Synthetic benchmark**: 2 toy repos (string_utils, validators), 2 bug types (boundary, string_validation). Does not represent real-world code complexity.
2. **Small model**: Qwen2.5-Coder-1.5B-Instruct is a 1.5B parameter model. Results may differ with larger models.
3. **RL = SFT**: REINFORCE did not improve over SFT on this benchmark, suggesting the task distribution may be too simple for RL to show benefit.
4. **Limited tool set**: 5 tools (read/search/edit/test/submit). Real code repair agents use more diverse tool suites.
5. **Short episodes**: Max 6 steps, 2 edits, 2 tests. Real debugging often requires more iterations.

## Testing

```bash
python -m pytest
ruff check .
```
