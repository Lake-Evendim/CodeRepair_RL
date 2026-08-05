#!/bin/bash
# Quick RL validation run using the dry-run limits in the quick configs.
set -e

cd "$(dirname "$0")/.."
mkdir -p logs

echo "=== Quick RL Dense ==="
PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=0 python scripts/train_rl_dense.py --config configs/rl_dense_quick.yaml --dry-run 2>&1 | tee logs/rl_dense_quick.log

echo "=== Quick RL Sparse ==="
PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES=0 python scripts/train_rl_sparse.py --config configs/rl_sparse_quick.yaml --dry-run 2>&1 | tee logs/rl_sparse_quick.log

echo "=== Quick validation done ==="
