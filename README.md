# MiniRepair-RL

RL for Test-Verifiable Code Repair Agents.

## Install

```bash
pip install -e '.[dev]'
```

## Test

```bash
python -m pytest
ruff check .
```

## Project Structure

```
minirepair/
  env/          # Tool layer, sandbox, CodeRepairEnv
  data/         # Benchmark tasks, SFT dataset
  agents/       # ReAct baseline, policy backends
  training/     # SFT and REINFORCE RL fine-tuning
  evaluation/   # Metrics, evaluator, failure analysis
configs/        # YAML configs for training
scripts/        # CLI entry points
reports/        # Generated reports
logs/           # Evaluation and training logs
tests/          # Unit tests
```
