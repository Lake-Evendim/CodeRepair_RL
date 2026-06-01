# Dataset Quality Report

## Train Split

**Tasks:** 80

### Repo Distribution

| Repo | Count |
|------|-------|
| string_utils | 40 |
| validators | 40 |

### Bug Type Distribution

| Bug Type | Count |
|----------|-------|
| boundary | 40 |
| string_validation | 40 |

### Test Counts

| Task | Public | Private | Quality/Hidden |
|------|--------|---------|----------------|
| task_0001 | 13 | 7 | 3 (quality) |
| task_0002 | 13 | 7 | 3 (quality) |
| task_0003 | 13 | 7 | 3 (quality) |
| task_0004 | 13 | 7 | 3 (quality) |
| task_0005 | 13 | 7 | 3 (quality) |
| ... | ... | ... | ... |

## Validation Split

**Tasks:** 20

### Repo Distribution

| Repo | Count |
|------|-------|
| string_utils | 10 |
| validators | 10 |

### Bug Type Distribution

| Bug Type | Count |
|----------|-------|
| boundary | 10 |
| string_validation | 10 |

### Test Counts

| Task | Public | Private | Quality/Hidden |
|------|--------|---------|----------------|
| task_0001 | 13 | 7 | 3 (quality) |
| task_0002 | 13 | 7 | 3 (quality) |
| task_0003 | 13 | 7 | 3 (quality) |
| task_0004 | 13 | 7 | 3 (quality) |
| task_0005 | 13 | 7 | 3 (quality) |
| ... | ... | ... | ... |

## Test Split

**Tasks:** 30

### Repo Distribution

| Repo | Count |
|------|-------|
| string_utils | 14 |
| validators | 16 |

### Bug Type Distribution

| Bug Type | Count |
|----------|-------|
| boundary | 16 |
| string_validation | 14 |

### Test Counts

| Task | Public | Private | Quality/Hidden |
|------|--------|---------|----------------|
| task_0001 | 13 | 7 | 5 (hidden) |
| task_0002 | 13 | 7 | 5 (hidden) |
| task_0003 | 13 | 7 | 5 (hidden) |
| task_0004 | 13 | 7 | 5 (hidden) |
| task_0005 | 13 | 7 | 5 (hidden) |
| ... | ... | ... | ... |

## Cross-Split Deduplication Analysis

### Gold Patch Pair Overlap

| Comparison | Overlap |
|------------|---------|
| train ∩ validation | 5 |
| train ∩ test | 5 |
| validation ∩ test | 1 |

### Bug Description Overlap

| Comparison | Overlap |
|------------|---------|
| train ∩ validation | 2 |
| train ∩ test | 3 |
| validation ∩ test | 0 |

## Summary

- **Total tasks:** 130
- **Train:** 80
- **Validation:** 20
- **Test:** 30
- **Gold patch pair duplicates across splits:** 11
