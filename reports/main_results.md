# Main Results

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

## logs/eval/sft_test_full

- Policy: `sft_qwen_lora`
- Method: `sft`
- Eval mode: `final_test`
- Total episodes: 30
- Included episodes: 30

### Metrics

| Metric | Value |
|--------|-------|
| Public pass rate | 16.67% |
| Private pass rate | 0.00% |
| Hidden pass rate | 70.00% |
| Avg invalid actions | 0.03 |
| Avg invalid edits | 0.60 |
| Avg regressions | 0.10 |
| Avg steps | 4.47 |
| Avg read calls | 1.00 |
| Avg search calls | 1.20 |
| Avg edit calls | 0.97 |
| Avg test calls | 0.30 |
| Submit-before-test rate | 66.67% |
| Avg guardrail violations | 0.63 |
| Avg repeated test call rate | 0.00% |
| Avg patch modified lines | 0.4 |
| Avg patch modified files | 0.3 |
| Public-hidden gap | +53.33% |

## logs/eval/rl_sparse_test_trained

- Policy: `rl_sparse_qwen_lora`
- Method: `rl_sparse`
- Eval mode: `final_test`
- Total episodes: 30
- Included episodes: 30

### Metrics

| Metric | Value |
|--------|-------|
| Public pass rate | 16.67% |
| Private pass rate | 0.00% |
| Hidden pass rate | 70.00% |
| Avg invalid actions | 0.07 |
| Avg invalid edits | 0.57 |
| Avg regressions | 0.10 |
| Avg steps | 4.47 |
| Avg read calls | 1.00 |
| Avg search calls | 1.20 |
| Avg edit calls | 0.93 |
| Avg test calls | 0.30 |
| Submit-before-test rate | 66.67% |
| Avg guardrail violations | 0.60 |
| Avg repeated test call rate | 0.00% |
| Avg patch modified lines | 0.4 |
| Avg patch modified files | 0.3 |
| Public-hidden gap | +53.33% |

## logs/eval/rl_dense_test_trained

- Policy: `rl_dense_qwen_lora`
- Method: `rl_dense`
- Eval mode: `final_test`
- Total episodes: 30
- Included episodes: 30

### Metrics

| Metric | Value |
|--------|-------|
| Public pass rate | 16.67% |
| Private pass rate | 0.00% |
| Hidden pass rate | 70.00% |
| Avg invalid actions | 0.03 |
| Avg invalid edits | 0.60 |
| Avg regressions | 0.07 |
| Avg steps | 4.40 |
| Avg read calls | 1.00 |
| Avg search calls | 1.17 |
| Avg edit calls | 0.97 |
| Avg test calls | 0.27 |
| Submit-before-test rate | 70.00% |
| Avg guardrail violations | 0.63 |
| Avg repeated test call rate | 0.00% |
| Avg patch modified lines | 0.4 |
| Avg patch modified files | 0.3 |
| Public-hidden gap | +53.33% |
