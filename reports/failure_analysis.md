# Failure Analysis

Total failed episodes: 73

## Primary Failure Distribution

| Category | Count | % of Failures | Description |
|----------|-------|---------------|-------------|
| invalid_edit | 34 | 46.6% | Edit was blocked by guardrails or exceeded edit budget |
| regression_error | 20 | 27.4% | Agent's edit introduced new test failures |
| tool_misuse | 10 | 13.7% | Agent spent budget on reads/searches without attempting any edit |
| invalid_action | 9 | 12.3% | Agent produced invalid JSON or unparseable action output |

## All Failure Categories (multi-label)

| Category | Occurrences |
|----------|-------------|
| localization_error | 54 |
| premature_submit | 37 |
| invalid_edit | 34 |
| regression_error | 21 |
| semantic_patch_error | 21 |
| tool_misuse | 13 |
| invalid_action | 9 |
| context_misunderstanding | 6 |

## Case Studies

### Case: task_0081 (sft)

- **Primary failure**: invalid_action
- **All categories**: invalid_action, premature_submit, tool_misuse
- **Steps**: 6
- **Edits**: 0
- **Tests**: 0
- **Invalid actions**: 1
- **Invalid edits**: 0
- **Termination**: submitted

**Trajectory summary:**
```
  Step 1: read_file({'path': 'src/string_utils.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> success
  Step 2: search_code({'path': None, 'old_text': None, 'new_text': None, 'query': 'capitalize_first_char', 'max_lines': 200, 'test_dir': 'tests'}) -> success
  Step 3: edit_file({'path': 'src/string_utils.py', 'old_text': 'capitalize_first_char', 'new_text': 'capitalize_first_character', 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  ... (3 more steps)
```

### Case: task_0091 (sft)

- **Primary failure**: invalid_action
- **All categories**: invalid_action, premature_submit, context_misunderstanding
- **Steps**: 5
- **Edits**: 0
- **Tests**: 0
- **Invalid actions**: 1
- **Invalid edits**: 0
- **Termination**: submitted

**Trajectory summary:**
```
  Step 1: read_file({'path': 'src/validators/dates.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  Step 2: read_file({'path': 'src/validators/dates.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  Step 3: read_file({'path': 'src/validators/dates.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  ... (3 more steps)
```

### Case: task_0089 (react)

- **Primary failure**: invalid_edit
- **All categories**: invalid_edit, regression_error, localization_error, semantic_patch_error
- **Steps**: 6
- **Edits**: 3
- **Tests**: 1
- **Invalid actions**: 0
- **Invalid edits**: 2
- **Termination**: max_steps

**Trajectory summary:**
```
  Step 1: read_file({'path': 'src/string_utils.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> success
  Step 2: search_code({'path': None, 'old_text': None, 'new_text': None, 'query': 'lowercase', 'max_lines': 200, 'test_dir': 'tests'}) -> success
  Step 3: edit_file({'path': 'src/string_utils.py', 'old_text': 'lowercase', 'new_text': 'capitalize', 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> success
  ... (3 more steps)
```

### Case: task_0083 (sft)

- **Primary failure**: invalid_edit
- **All categories**: invalid_edit, premature_submit, localization_error
- **Steps**: 4
- **Edits**: 1
- **Tests**: 0
- **Invalid actions**: 0
- **Invalid edits**: 1
- **Termination**: submitted

**Trajectory summary:**
```
  Step 1: read_file({'path': 'src/string_utils.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> success
  Step 2: edit_file({'path': 'src/string_utils.py', 'old_text': 'return s[: max_len - 3] + "..."}', 'new_text': 'return s[: max_len - 3] + "."', 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  Step 3: search_code({'path': None, 'old_text': None, 'new_text': None, 'query': 'return s[: max_len - 3] + "..."', 'max_lines': 200, 'test_dir': 'tests'}) -> success
  ... (3 more steps)
```

### Case: task_0082 (react)

- **Primary failure**: regression_error
- **All categories**: regression_error, localization_error, semantic_patch_error
- **Steps**: 6
- **Edits**: 1
- **Tests**: 2
- **Invalid actions**: 0
- **Invalid edits**: 0
- **Termination**: submitted

**Trajectory summary:**
```
  Step 1: read_file({'path': 'src/string_utils.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> success
  Step 2: search_code({'path': None, 'old_text': None, 'new_text': None, 'query': 'count_substring', 'max_lines': 200, 'test_dir': 'tests'}) -> success
  Step 3: edit_file({'path': 'src/string_utils.py', 'old_text': 'return s.count(sub)', 'new_text': 'return s.count(sub) + 1', 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> success
  ... (3 more steps)
```

### Case: task_0088 (react)

- **Primary failure**: regression_error
- **All categories**: regression_error, localization_error, semantic_patch_error
- **Steps**: 4
- **Edits**: 1
- **Tests**: 1
- **Invalid actions**: 0
- **Invalid edits**: 0
- **Termination**: submitted

**Trajectory summary:**
```
  Step 1: read_file({'path': 'src/string_utils.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> success
  Step 2: edit_file({'path': 'src/string_utils.py', 'old_text': 'if idx == -1:', 'new_text': 'if idx == -1 or idx >= max_len - len(sub):', 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> success
  Step 3: run_tests({'path': None, 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  ... (1 more steps)
```

### Case: task_0091 (react)

- **Primary failure**: tool_misuse
- **All categories**: tool_misuse
- **Steps**: 6
- **Edits**: 0
- **Tests**: 0
- **Invalid actions**: 0
- **Invalid edits**: 0
- **Termination**: max_steps

**Trajectory summary:**
```
  Step 1: read_file({'path': 'src/validators/dates.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  Step 2: read_file({'path': 'src/validators/dates.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  Step 3: read_file({'path': 'src/validators/dates.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  ... (3 more steps)
```

### Case: task_0092 (react)

- **Primary failure**: tool_misuse
- **All categories**: tool_misuse
- **Steps**: 6
- **Edits**: 0
- **Tests**: 0
- **Invalid actions**: 0
- **Invalid edits**: 0
- **Termination**: max_steps

**Trajectory summary:**
```
  Step 1: read_file({'path': 'src/validators/__init__.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  Step 2: read_file({'path': 'src/validators/__init__.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  Step 3: read_file({'path': 'src/validators/__init__.py', 'old_text': None, 'new_text': None, 'query': None, 'max_lines': 200, 'test_dir': 'tests'}) -> error
  ... (3 more steps)
```
