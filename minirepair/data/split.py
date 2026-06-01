"""Split assignment for benchmark tasks.

Assigns BugVariants to train/validation/test splits with:
- Stratified sampling by (repo_type, bug_type, function_name)
- No variant reuse across splits
- Deterministic with seed
"""

from __future__ import annotations

import random
from collections import defaultdict

from minirepair.data.bug_catalog import BugVariant


def assign_splits(
    variants: list[BugVariant],
    train_per_combo: int = 5,
    val_per_combo: int = 1,
    test_candidates_per_combo: int = 2,
    test_total: int = 30,
    seed: int = 42,
) -> dict[str, list[BugVariant]]:
    """Assign variants to splits.

    Returns dict with keys: train, validation, test.
    Each (repo_type, bug_type, function_name) combination gets:
    - train_per_combo variants for train
    - val_per_combo variants for validation
    - test_candidates_per_combo candidates for test
    Then test is stratified-sampled to test_total.
    """
    rng = random.Random(seed)

    # Group by (repo_type, bug_type, function_name)
    groups: dict[tuple, list[BugVariant]] = defaultdict(list)
    for v in variants:
        key = (v.repo_type, v.bug_type, v.function_name)
        groups[key].append(v)

    train: list[BugVariant] = []
    val: list[BugVariant] = []
    test_candidates: list[BugVariant] = []

    for key, group in sorted(groups.items()):
        shuffled = list(group)
        rng.shuffle(shuffled)

        train.extend(shuffled[:train_per_combo])
        val.extend(shuffled[train_per_combo:train_per_combo + val_per_combo])
        test_candidates.extend(shuffled[
            train_per_combo + val_per_combo:
            train_per_combo + val_per_combo + test_candidates_per_combo
        ])

    # Stratified sampling from test_candidates to get test_total
    # Group test_candidates by (repo_type, bug_type, function_name)
    test_groups: dict[tuple, list[BugVariant]] = defaultdict(list)
    for v in test_candidates:
        key = (v.repo_type, v.bug_type, v.function_name)
        test_groups[key].append(v)

    # Shuffle each group
    for group in test_groups.values():
        rng.shuffle(group)

    # First pass: take 1 from each group
    test: list[BugVariant] = []
    capacities: dict[tuple, int] = {}
    for key, group in test_groups.items():
        take = min(1, len(group))
        test.extend(group[:take])
        capacities[key] = len(group) - take

    # Second pass: distribute remaining to groups with capacity
    remaining = test_total - len(test)
    keys_with_capacity = [k for k, c in capacities.items() if c > 0]
    rng.shuffle(keys_with_capacity)
    for key in keys_with_capacity:
        if remaining <= 0:
            break
        group = test_groups[key]
        already_taken = len(group) - capacities[key]
        can_take = min(capacities[key], remaining)
        test.extend(group[already_taken:already_taken + can_take])
        remaining -= can_take

    # Verify no overlap
    train_ids = {v.variant_id for v in train}
    val_ids = {v.variant_id for v in val}
    test_ids = {v.variant_id for v in test}
    assert train_ids.isdisjoint(val_ids), "train/val overlap"
    assert train_ids.isdisjoint(test_ids), "train/test overlap"
    assert val_ids.isdisjoint(test_ids), "val/test overlap"

    return {"train": train, "validation": val, "test": test}
