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

    Deduplication: variants sharing the same gold_patch (fix_old, fix_new)
    are reduced to a single representative before splitting, ensuring no
    cross-split gold_patch pair overlap.
    """
    rng = random.Random(seed)

    # Deduplicate by gold_patch pair (fix_old, fix_new) to prevent cross-split overlap
    seen_patches: set[tuple[str, str]] = set()
    deduped: list[BugVariant] = []
    for v in variants:
        patch_key = (v.fix_old, v.fix_new)
        if patch_key not in seen_patches:
            seen_patches.add(patch_key)
            deduped.append(v)

    if len(deduped) < len(variants):
        print(f"  Deduplication: {len(variants)} -> {len(deduped)} variants "
              f"(removed {len(variants) - len(deduped)} with duplicate gold patches)")

    # Group by (repo_type, bug_type, function_name)
    groups: dict[tuple, list[BugVariant]] = defaultdict(list)
    for v in deduped:
        key = (v.repo_type, v.bug_type, v.function_name)
        groups[key].append(v)

    train: list[BugVariant] = []
    val: list[BugVariant] = []
    test_candidates: list[BugVariant] = []

    for key, group in sorted(groups.items()):
        shuffled = list(group)
        rng.shuffle(shuffled)
        n = len(shuffled)

        # Reserve validation and test candidates first, then assign rest to train
        actual_val = min(val_per_combo, n)
        remaining_after_val = n - actual_val
        actual_test = min(test_candidates_per_combo, remaining_after_val)
        actual_train = n - actual_val - actual_test

        # Clamp train to requested amount
        actual_train = min(actual_train, train_per_combo)

        val.extend(shuffled[:actual_val])
        test_candidates.extend(shuffled[actual_val:actual_val + actual_test])
        train.extend(shuffled[actual_val + actual_test:actual_val + actual_test + actual_train])

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
