# MiniRepair-RL: Technical Report

## 1. Problem Formulation

We formalize code repair as a finite-horizon Markov Decision Process (MDP). Given a buggy codebase and a set of failing tests, an agent must diagnose the bug and produce a correct patch within a limited number of interaction steps.

**Task**: Agent receives a buggy repository with passing/failing public tests. It must produce an edit that fixes the bug without introducing regressions, verified by private (and hidden) tests unseen during the episode.

**Evaluation**: Success is measured by hidden test pass rate on a held-out test split, using `EvalMode.FINAL_TEST`. Validation uses private tests (`EvalMode.VALIDATION_SELECTION`) for checkpoint selection.

## 2. MDP Design

### State
The agent observes:
- Tool call results (file contents, search matches, test output)
- Remaining budget (steps, edits, tests)
- Tool history summary

The agent does NOT observe: private test content, hidden test content, gold patches, or reward details.

### Action
Structured JSON with a single tool call per step:

```json
{
  "thought": "brief reasoning",
  "tool": "edit_file",
  "arguments": {
    "path": "src/string_utils.py",
    "old_text": "buggy code",
    "new_text": "fixed code"
  }
}
```

Tools: `read_file`, `search_code`, `edit_file`, `run_tests`, `submit`.

### Reward

**Sparse**: +1.0 if all private tests pass at terminal, 0.0 otherwise, -1.0 for severe guardrail violation.

**Dense**: Adds shaping signals for valid edits (+0.1), invalid actions (-0.3), invalid edits (-0.5), regressions (-0.2), first public test pass (+0.2), and step penalties (-0.05/call).

### Termination
Episode ends when: agent calls `submit`, max steps reached (6), max edits exhausted (2), max tests exhausted (2), or 3 consecutive invalid actions.

## 3. Tool Interface

| Tool | Constraints |
|------|------------|
| `read_file` | Max 200 lines, repo files only |
| `search_code` | Searches `src/` only |
| `edit_file` | Single-file, old_text must appear exactly once, max 5 lines changed, max 2 per episode |
| `run_tests` | Runs public tests only |
| `submit` | Signals completion |

### Guardrails
- Forbidden paths: `tests/`, `tests_private/`, `tests_hidden/`, `tests_quality_holdout/`, `pyproject.toml`, `conftest.py`
- Blocked patterns: `pytest.skip`, `pytest.xfail`, assert deletion
- Heuristic detection: hardcoded test case returns, large code deletion, if-branch on specific test literals

## 4. Benchmark Design

### Scale
- 130 tasks total: 80 train, 20 validation, 30 test
- 140 unique bug variants (7 per function x bug_type x repo_type)
- 2 repos: `string_utils` (5 functions), `validators` (5 functions)
- 2 bug types: `boundary`, `string_validation`

### Test Structure
- Public tests: visible to agent, 13 per task
- Private tests: hidden from agent, 7 per task (reward signal)
- Quality holdout tests: 3 per task in train/validation (dataset quality validation only)
- Hidden tests: 5 per task in test split (final evaluation only)

### Split Isolation
- Train/validation: no `tests_hidden/` directory
- Test: `tests_hidden/` accessible only via `EvalMode.FINAL_TEST`
- Cross-split deduplication: zero gold patch pair overlap between any splits

### Bug Variant Catalog
Each function has 7 variants covering different edge cases. For example, `truncate_string` variants include: off-by-one in length check, wrong suffix, missing edge case for exact length, boundary at zero, etc.

## 5. Reward Design

### Sparse Reward
Terminal-only signal: +1.0 if all private tests pass, 0.0 otherwise. Simple but provides no learning signal for partial progress.

### Dense Reward
Multi-signal shaping:
- **Edit quality**: +0.1 per valid edit, -0.5 per invalid edit
- **Action quality**: -0.3 per invalid action (bad JSON, unparseable)
- **Regression**: -0.2 if previously passing public tests now fail
- **Progress**: +0.2 when first public test passes, +1.0 for full private pass
- **Efficiency**: -0.05 per extra tool call
- **Safety**: -1.0 for severe guardrail violation (terminal)

### Anti-Hacking Measures
- No gold patch similarity reward
- No changed_files oracle
- No patch minimality in reward (only as evaluation metric)
- Guardrails block test modification, assert deletion, skip/xfail injection
- Heuristic detection of hardcoded returns targeting public test cases

## 6. Training Setup

### SFT (Phase 6)
- **Model**: Qwen2.5-Coder-1.5B-Instruct
- **Method**: LoRA (r=16, alpha=32, dropout=0.05) via TRL SFTTrainer
- **Data**: 648 training samples, 72 dev samples, from 80 train tasks only
- **Hyperparameters**: batch 4, gradient accumulation 4, lr 2e-4, 3 epochs, max_seq_length 1024
- **Convergence**: loss 1.934 -> 0.141, accuracy 62.4% -> 96.0%
- **Hardware**: RTX 4090 24GB

### REINFORCE RL (Phase 7)
- **Initialization**: From SFT adapter
- **Method**: REINFORCE with moving-average baseline (momentum 0.9)
- **Policy gradient**: `loss = -advantage.detach() * trajectory_log_prob`
- **Log-prob**: Re-computed with gradient from current policy (not detached rollout logs)
- **Hyperparameters**: lr 1e-5, 2 rollouts/task, 3 epochs
- **Both sparse and dense reward modes trained separately**

## 7. Experiments

### Methods Compared
All use Qwen2.5-Coder-1.5B-Instruct as base model:

1. **ReAct**: Zero-shot prompt + tool-use loop, no training
2. **SFT**: LoRA fine-tuned on gold trajectories from train split
3. **RL Sparse**: REINFORCE with sparse reward, starting from SFT adapter
4. **RL Dense**: REINFORCE with dense reward, starting from SFT adapter

### Evaluation Protocol
- Validation (20 tasks): `EvalMode.VALIDATION_SELECTION`, private tests for checkpoint selection
- Test (30 tasks): `EvalMode.FINAL_TEST`, hidden tests for frozen final evaluation
- Metrics: public/hidden pass rate, invalid action/edit rate, regression rate, avg steps, guardrail violations, patch minimality

## 8. Results

### Main Results (Test Split, 30 Tasks)

| Method | Hidden Pass | Public Pass | Invalid Edit | Regression | Avg Steps |
|--------|:-----------:|:-----------:|:------------:|:----------:|:---------:|
| ReAct | 60.0% | 3.3% | 0.13 | 0.20 | 5.53 |
| SFT | 70.0% | 16.7% | 0.60 | 0.10 | 4.47 |
| RL Sparse | 70.0% | 16.7% | 0.57 | 0.10 | 4.47 |
| RL Dense | 70.0% | 16.7% | 0.60 | 0.07 | 4.40 |

### Key Findings
1. SFT improves hidden pass rate by +10% over ReAct (60% -> 70%)
2. RL (both sparse and dense) does not improve hidden pass rate over SFT on this benchmark
3. RL Dense slightly reduces regressions (0.07 vs 0.10) and avg steps (4.40 vs 4.47) compared to SFT
4. Large public-hidden gap (~53%) indicates generalization challenge
5. The benchmark may be too simple for RL to show clear benefit over SFT

### Reward Ablation

| Reward | Val Private Pass | Test Hidden Pass | Invalid Action | Invalid Edit | Avg Steps |
|--------|:----------------:|:----------------:|:--------------:|:------------:|:---------:|
| Sparse | 60.0% | 70.0% | 0.15 | 0.45 | 4.85 |
| Dense | 60.0% | 70.0% | 0.15 | 0.45 | 4.85 |

### SFT Training Convergence

| Epoch | Loss | Accuracy |
|:-----:|:----:|:--------:|
| 1 | 1.934 | 62.4% |
| 2 | 0.488 | 89.2% |
| 3 | 0.141 | 96.0% |

## 9. Failure Analysis

177 failed episodes analyzed across all methods.

### Failure Distribution

| Category | Count | % of Failures |
|----------|:-----:|:-------------:|
| Invalid edit (guardrail blocked) | 90 | 50.8% |
| Regression error | 31 | 17.5% |
| Tool misuse | 27 | 15.3% |
| Invalid action (bad JSON) | 13 | 7.3% |
| Localization error | 10 | 5.6% |
| Premature submit | 6 | 3.4% |

### Multi-label Categories

| Category | Occurrences |
|----------|:-----------:|
| Localization error | 137 |
| Premature submit | 98 |
| Invalid edit | 90 |
| Semantic patch error | 42 |
| Regression error | 35 |
| Tool misuse | 30 |
| Invalid action | 13 |
| Context misunderstanding | 10 |

### Representative Cases
- **task_0081 (SFT)**: Agent produced invalid JSON action, never attempted edit. Premature submit.
- **task_0089 (ReAct)**: Agent attempted 3 edits, 2 blocked by guardrails. Wrong old_text matched multiple locations.
- **task_0082 (ReAct)**: Correct localization but wrong fix (+1 instead of correct logic), introduced regression.
- **task_0091 (ReAct)**: Agent read same file 6 times without attempting any edit. Pure tool misuse.

## 10. Threats to Validity

1. **Synthetic benchmark**: Only 2 toy repos with simple string/validation functions. Real codebases have complex dependencies, multi-file bugs, and subtle logic errors not captured here.
2. **Scale**: 130 tasks is small. Results may not generalize to larger, more diverse benchmarks.
3. **RL plateau**: REINFORCE did not improve over SFT. This may indicate: (a) the task is too simple for RL to show benefit, (b) the reward signal is too sparse/noisy, or (c) the exploration budget is insufficient.
4. **Single model**: Only tested with Qwen2.5-Coder-1.5B-Instruct. Larger models may show different SFT/RL dynamics.
5. **Public-hidden gap**: The ~53% gap between public and hidden pass rates suggests the benchmark may have distribution shift between test tiers, or the agent overfits to public test patterns.
6. **Identical RL/SFT**: Both RL variants match SFT exactly, suggesting the SFT adapter may already be at a local optimum that REINFORCE cannot escape with the current setup.
