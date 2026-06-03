# Release Readiness Checklist

Generated: 2026-06-03

## 1. README Commands vs Real Scripts

| README Command | Script | Status |
|---------------|--------|:------:|
| `python scripts/generate_tasks.py --seed 42 --output benchmarks` | `scripts/generate_tasks.py` | PASS |
| `python scripts/validate_tasks.py --tasks benchmarks/train benchmarks/validation benchmarks/test` | `scripts/validate_tasks.py` | PASS |
| `python scripts/evaluate.py --method react --split validation --eval-mode validation_selection --policy qwen_base --model Qwen/Qwen2.5-Coder-1.5B-Instruct --output ...` | `scripts/evaluate.py` | PASS |
| `python scripts/evaluate.py --method react --split test --eval-mode final_test --policy qwen_base --model Qwen/Qwen2.5-Coder-1.5B-Instruct --output ...` | `scripts/evaluate.py` | PASS |
| `python scripts/build_sft_dataset.py --benchmark-root benchmarks --source-split train --dev-fraction 0.1 --seed 42 --output-train ... --output-dev ...` | `scripts/build_sft_dataset.py` | PASS |
| `python scripts/train_sft.py --config configs/sft.yaml` | `scripts/train_sft.py` | PASS |
| `python scripts/train_sft.py --config configs/sft.yaml --dry-run` | `scripts/train_sft.py` | PASS |
| `python scripts/train_rl_sparse.py --config configs/rl_sparse.yaml` | `scripts/train_rl_sparse.py` | PASS |
| `python scripts/train_rl_dense.py --config configs/rl_dense.yaml` | `scripts/train_rl_dense.py` | PASS |
| `python scripts/evaluate.py --method sft --split validation/test --eval-mode ... --adapter ... --output ...` | `scripts/evaluate.py` | PASS |
| `python scripts/evaluate.py --method rl_sparse --split validation/test --eval-mode ... --adapter ... --output ...` | `scripts/evaluate.py` | PASS |
| `python scripts/evaluate.py --method rl_dense --split validation/test --eval-mode ... --adapter ... --output ...` | `scripts/evaluate.py` | PASS |
| `python scripts/summarize_metrics.py --inputs ... --require-main-comparable --output reports/main_results.md` | `scripts/summarize_metrics.py` | PASS |
| `python scripts/compare_rewards.py --validation-inputs ... --test-inputs ... --output reports/reward_ablation.md` | `scripts/compare_rewards.py` | PASS |
| `python scripts/analyze_failures.py --inputs ... --output reports/failure_analysis.md` | `scripts/analyze_failures.py` | PASS |

All CLI flags verified against `--help` output.

## 2. Config Files

| Config | Referenced By | Exists | Loadable |
|--------|--------------|:------:|:--------:|
| `configs/sft.yaml` | `train_sft.py` | PASS | PASS |
| `configs/rl_sparse.yaml` | `train_rl_sparse.py` | PASS | PASS |
| `configs/rl_dense.yaml` | `train_rl_dense.py` | PASS | PASS |

## 3. Reports vs Real Metrics

| Report | Input Source | Status |
|--------|-------------|:------:|
| `reports/main_results.md` | `logs/eval/react_test_full`, `sft_test_full`, `rl_sparse_test_full`, `rl_dense_test_full` | PASS |
| `reports/reward_ablation.md` | `logs/eval/rl_sparse_validation_full`, `rl_dense_validation_full`, `rl_sparse_test_full`, `rl_dense_test_full` | PASS |
| `reports/failure_analysis.md` | All eval log directories | PASS |
| `reports/dataset_report.md` | Benchmark task metadata | PASS |

## 4. Data Boundary Compliance

| Check | Status |
|-------|:------:|
| SFT data only from train split | PASS |
| `build_sft_dataset.py` rejects `--source-split validation` and `--source-split test` | PASS |
| No `tests_hidden/` in train/validation splits | PASS |
| `tests_hidden/` only accessible via `EvalMode.FINAL_TEST` on test split | PASS |
| Agent observation excludes private/hidden test content | PASS |
| Reward function requires explicit `EvalMode` for private/hidden access | PASS |
| No gold patch in prompt, agent observation, or SFT input | PASS |

## 5. .gitignore Coverage

| Item | Covered |
|------|:-------:|
| `outputs/` (LoRA adapters) | PASS |
| `*.pt`, `*.bin`, `*.safetensors` (model weights) | PASS |
| `logs/*` (evaluation logs) | PASS |
| `*.jsonl`, `*.csv` (data files) | PASS |
| `.env`, `*.pem`, `*.key` (secrets) | PASS |
| `__pycache__/`, `*.egg-info/` | PASS |

## 6. Code Quality

| Check | Status |
|-------|:------:|
| `python -m pytest` | PASS (222 tests) |
| `ruff check .` | PASS |

## 7. Known Issues

1. **`main_results.md` metadata**: Some fields show "unknown" for policy/method/eval_mode. This is a cosmetic issue in `summarize_metrics.py` not reading summary.json metadata correctly. Does not affect metric values.
2. **RL = SFT performance**: REINFORCE did not improve over SFT. Documented in technical report as a limitation, not a bug.
