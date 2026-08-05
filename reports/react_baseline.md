# ReAct Baseline Report

## logs/eval/react_validation_full

- Policy: `qwen_base`
- Method: `react`
- Eval mode: `validation_selection`
- Total episodes: 20
- Included episodes: 20

### Metrics

| Metric | Value |
|--------|-------|
| Public pass rate | 5.00% |
| Private pass rate | 60.00% |
| Hidden pass rate | 0.00% |
| Avg invalid actions | 0.00 |
| Avg invalid edits | 0.65 |
| Avg regressions | 0.30 |
| Avg steps | 5.90 |
| Avg read calls | 3.60 |
| Avg search calls | 0.80 |
| Avg edit calls | 1.00 |
| Avg test calls | 0.40 |
| Submit-before-test rate | 0.00% |
| Avg guardrail violations | 0.65 |
| Avg repeated test call rate | 2.50% |
| Avg patch modified lines | 0.3 |
| Avg patch modified files | 0.2 |
| Public-private gap | +55.00% |

## logs/eval/react_test_full

- Policy: `qwen_base`
- Method: `react`
- Eval mode: `final_test`
- Total episodes: 30
- Included episodes: 30

### Metrics

| Metric | Value |
|--------|-------|
| Public pass rate | 3.33% |
| Private pass rate | 0.00% |
| Hidden pass rate | 60.00% |
| Avg invalid actions | 0.00 |
| Avg invalid edits | 0.13 |
| Avg regressions | 0.20 |
| Avg steps | 5.53 |
| Avg read calls | 3.83 |
| Avg search calls | 0.47 |
| Avg edit calls | 0.50 |
| Avg test calls | 0.37 |
| Submit-before-test rate | 0.00% |
| Avg guardrail violations | 0.13 |
| Avg repeated test call rate | 0.00% |
| Avg patch modified lines | 0.4 |
| Avg patch modified files | 0.4 |
| Public-hidden gap | +56.67% |
