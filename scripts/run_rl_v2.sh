#!/bin/bash
# Run RL dense then sequential RL sparse with improved configs.
set -e

cd "$(dirname "$0")/.."
mkdir -p logs

echo "=== Starting RL Dense v2 ==="
PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=0 python scripts/train_rl_dense.py --config configs/rl_dense.yaml 2>&1 | tee logs/rl_dense_v2.log

echo "=== Starting RL Sparse v2 ==="
PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=0 python scripts/train_rl_sparse.py --config configs/rl_sparse.yaml 2>&1 | tee logs/rl_sparse_v2.log

echo "=== All done ==="
