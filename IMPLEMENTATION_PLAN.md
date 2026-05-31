# MiniRepair-RL：Claude Code 全链路阶段化实现方案
> 目标：使用 Claude Code 从零实现 **MiniRepair-RL: RL for Test-Verifiable Code Repair Agents**。本方案将项目拆解为可独立验收的短任务，每个任务都包含人类决策、Claude Code 执行内容、可直接复制到 Claude Code 交互终端的指令，以及 Definition of Done。
>
> 
>
> 修订说明：本版根据《MiniRepair-RL 项目方案：简历导向收敛版》收紧了第一版边界，明确正式实验需尽量使用同一 base model，限制 private/hidden/gold patch 的使用范围，并将部分工程规范与复杂 guardrail 检测降级为可选或 heuristic，避免范围膨胀。
>
> 二次修订说明：根据审阅意见，修正最终命令清单中从 validation split 构造 SFT dataset 的错误；统一 hidden tests 使用边界；强化 MockPolicy 只能用于 smoke test 且不得进入主结果表；再次明确 mypy、pre-commit、CI-like checks 等工程规范均为可选，不得阻塞核心闭环。
>
> 三次修订说明：进一步加入实验边界与防泄漏硬约束，强制主实验使用同一 base model，明确 hidden/private/test split 的代码级使用边界，补充 REINFORCE token-level log-prob 训练要求，并加入 synthetic benchmark split 去重与 leakage audit。
>
> 四次修订说明：根据最终审阅意见，补充统一 EvalMode 访问边界，明确 hard leakage 才阻塞、near-duplicate 仅 warning；将 Phase 7 拆分为 reward / rollout / log-prob / single-update / full-loop 五个 Claude Code 子任务；修正最终评估命令，显式指定 ReAct 的 Qwen base model，并让 reward ablation 同时读取 validation 与 test logs。
>
>
> 五次修订说明：根据最终审阅意见收紧执行口径：hidden tests 严格只存在于 test split 并只能在 `EvalMode.FINAL_TEST` 下访问；统一使用 `scripts/evaluate.py` 进行 SFT/RL 评估；所有 test split 最终评估命令必须显式传入 `--eval-mode final_test`；REINFORCE update 阶段必须用当前 policy 重新 forward 计算带梯度 action-token log-prob；主结果汇总禁止使用宽泛 `logs/eval/*` 输入，改为显式列出可比较实验日志。
>

---

## 0. 项目定义
### 0.1 项目名称
**MiniRepair-RL: RL for Test-Verifiable Code Repair Agents**

### 0.2 项目描述
MiniRepair-RL 是一个小规模、可复现、可训练、可评测的代码修复 Agent RL 闭环。项目将代码修复任务形式化为有限步长 MDP，Agent 通过结构化工具调用执行多步调试：

```latex
read_file / search_code / edit_file / run_tests / submit
```

系统使用 synthetic Python bug benchmark、public/private/hidden test split、execution-based reward、anti-reward-hacking guardrails，对比 ReAct、SFT、SFT+RL 是否能改善代码修复 Agent 的工具使用质量和 hidden-test 泛化表现。

### 0.3 核心功能
```latex
1. 构建 synthetic Python bug benchmark；
2. 构建交互式 CodeRepairEnv；
3. 实现结构化工具调用；
4. 实现 constrained search-replace patch interface；
5. 实现 public/private/hidden tests 隔离；
6. 实现 sparse/dense execution-based reward；
7. 实现 anti-reward-hacking guardrails；
8. 实现 ReAct baseline；
9. 构造 SFT gold trajectories；
10. 实现 LoRA/QLoRA SFT warmup；
11. 实现轻量级 REINFORCE RL fine-tuning；
12. 实现 evaluation、metrics、failure analysis、technical report。
```

### 0.4 技术栈
```latex
Language: Python 3.11+
Package manager: uv 或 pip
Testing: pytest
Sandbox: tempfile + subprocess + timeout
Search: pathlib + regex
Config: YAML
Schema validation: pydantic
Logging: JSONL + CSV
Model: Qwen2.5-Coder-1.5B-Instruct
Fine-tuning: LoRA / QLoRA
SFT: TRL SFTTrainer
RL: custom REINFORCE with moving-average baseline
Visualization: matplotlib
CLI: argparse（typer 可选）
Quality: pytest + ruff（mypy、pre-commit、CI-like checks 可选，不应阻塞核心闭环）
```

---

## 1. 总体阶段划分
| 阶段 | 名称 | 主要交付物 |
| --- | --- | --- |
| Phase 0 | 项目脚手架与工程规范 | repo structure、pyproject、pytest、ruff；mypy/pre-commit/CI-like checks 可选 |
| Phase 1 | Benchmark 最小闭环 | mini repo templates、task schema、20 个 seed tasks |
| Phase 2 | 工具层与沙箱 | read/search/edit/test/submit、guardrails、sandbox |
| Phase 3 | CodeRepairEnv | reset/step/render/replay、trajectory logging |
| Phase 4 | Full Benchmark | 130 tasks、split、generator、dataset validation |
| Phase 5 | ReAct Baseline | action parser、prompt、agent loop、baseline metrics |
| Phase 6 | SFT 数据与训练 | gold trajectory builder、SFT dataset、LoRA SFT |
| Phase 7 | Reward 与 RL Fine-tuning | reward、rollout、token log-prob、single-update、完整 REINFORCE、sparse/dense ablation |
| Phase 8 | Evaluation 与 Failure Analysis | metrics tables、failure taxonomy、case studies |
| Phase 9 | 报告、README、简历材料 | reproducible scripts、technical report、resume bullets |


---

## 全局强制约束：实验边界、防泄漏与主结果口径
本节约束优先级高于后续各 Phase 的局部指令。若后续实现细节与本节冲突，以本节为准。

### 2.1 主实验公平性
正式主结果表只能比较同一 base model 家族下的方法：

```latex
1. react_qwen_base；
2. sft_qwen_lora；
3. rl_sparse_qwen_lora；
4. rl_dense_qwen_lora。
```

外部 API、Claude、OpenAI-compatible API、MockPolicy、GoldPolicy、OraclePolicy 只能作为 smoke test 或 reference baseline，不得进入 `reports/main_results.md`、`reports/reward_ablation.md` 或 README 的正式主结果表。

`summarize_metrics.py` 默认必须拒绝混入以下结果：

```latex
- policy_type in {mock, gold, oracle};
- excluded_from_main_results=true；
- base_model_family 与 Qwen2.5-Coder-1.5B-Instruct 不一致；
- method_name 包含 external_api / claude_reference / openai_reference。
```

除非显式使用 `--allow-non-comparable-baselines`，否则这些结果只能进入 reference appendix。

### 2.2 SFT 数据边界
SFT supervised targets 只能从 project train split 的 `metadata.gold_patch` 离线构造。

```latex
允许：
- train split gold_patch -> SFT target action；
- train split 内部再划分 sft_train / sft_dev。

禁止：
- validation split gold_patch -> SFT target；
- test split gold_patch -> SFT target；
- gold_patch 出现在 prompt、Agent observation、runtime state、trajectory observation、validation/test inference context；
- private/hidden tests 内容进入 prompt 或 SFT input。
```

`build_sft_dataset.py` 必须在代码层面拒绝 `--source-split validation` 和 `--source-split test`。

### 2.3 Private / Hidden tests 使用边界
代码层面必须区分三类测试：

```latex
1. public_tests
   - Agent 可运行；
   - 可进入 observation；
   - 可用于 public recovery reward。

2. private_tests
   - Agent 不可读取、不可运行、不可见；
   - train/validation 阶段可用于 terminal reward 和 checkpoint selection；
   - 可写入 training/evaluation log，但不得进入 Agent observation。

3. hidden_tests
   - Agent 不可读取、不可运行、不可见；
   - 严格只存在于 test split；
   - 只能在 split == test 且 EvalMode.FINAL_TEST 时用于最终 frozen evaluation；
   - 不得用于训练、模型选择、reward ablation 调参、prompt 构造、SFT target 构造或 checkpoint selection。
```

硬性目录口径：

```latex
1. benchmarks/train/** 不得包含 tests_hidden/；
2. benchmarks/validation/** 不得包含 tests_hidden/；
3. benchmarks/test/** 可以包含 tests_hidden/，但只能由 final frozen evaluation 读取；
4. 若需要为 train/validation 保存额外离线质量验证样例，必须命名为 tests_quality_holdout/，不得命名为 tests_hidden/；
5. tests_quality_holdout/ 只能由 validate_tasks.py 在 EvalMode.DATASET_VALIDATION 下读取，其结果不得进入 training、checkpoint selection、reward ablation、prompt、SFT target 或主结果表。
```

必须补充测试：

```latex
1. reward.py 在 train/validation/test training mode 下不能读取 tests_hidden/ 或 tests_quality_holdout/；
2. evaluator.py 只有 `--split test --eval-mode final_test` 才能计算 hidden_pass_rate；
3. evaluator.py 对 validation split 必须使用 EvalMode.VALIDATION_SELECTION，只能计算 private_pass_rate；
4. summarize_metrics.py 对 validation split 不输出 hidden_pass_rate，改输出 private_pass_rate；
5. render_state() 和 step() observation 中不得包含 private/hidden/quality_holdout 路径、测试名、traceback 或 reward 明细。
```

建议在代码层统一使用显式评估模式，避免不同脚本各自用字符串判断造成泄漏：

```python
from enum import Enum

class EvalMode(str, Enum):
    TRAIN_REWARD = "train_reward"              # train split，private terminal reward
    VALIDATION_SELECTION = "validation_selection"  # validation split，private pass 做 checkpoint selection
    FINAL_TEST = "final_test"                  # 仅 test split，hidden pass 做 frozen final evaluation
    DATASET_VALIDATION = "dataset_validation"  # 离线验证 benchmark 质量，可检查 tests_quality_holdout/ 或 test hidden
```

硬性要求：

```latex
1. EvalMode.TRAIN_REWARD 不得访问 tests_hidden/ 或 tests_quality_holdout/；
2. EvalMode.VALIDATION_SELECTION 不得访问 tests_hidden/ 或 tests_quality_holdout/；
3. EvalMode.FINAL_TEST 仅允许 split == test 时访问 tests_hidden/；
4. EvalMode.DATASET_VALIDATION 可验证 public/private/tests_quality_holdout 或 test hidden tests，但其结果不得进入 training、checkpoint selection、prompt、SFT target 或 reward ablation；
5. 所有读取 tests_private/、tests_hidden/ 或 tests_quality_holdout/ 的函数必须显式接收 EvalMode，禁止隐式 glob 全部 tests。
```

### 2.4 Validation 与 Test 指标命名
validation 阶段使用 private tests 做模型选择；test 阶段使用 hidden tests 做最终报告。指标命名必须避免混淆。

```latex
Validation metrics:
- public_pass_rate；
- private_pass_rate；
- public_private_gap。

Test metrics:
- public_pass_rate；
- hidden_pass_rate；
- public_hidden_gap。
```

`reward_ablation.md` 使用：

```latex
Reward | Val Private Pass | Test Hidden Pass | Invalid Action | Invalid Edit | Avg Steps
```

### 2.5 REINFORCE 必须是真实 policy-gradient 更新
REINFORCE 实现必须基于模型生成 action tokens 的 log-prob 做 policy-gradient，不允许只记录 reward 或只做 heuristic reranking。

每条 rollout 必须保存：

```latex
1. prompt token ids；
2. generated action token ids；
3. attention mask；
4. raw model output；
5. parsed action；
6. per-step action token log_prob；
7. trajectory sum_log_prob；
8. terminal return；
9. moving-average baseline；
10. advantage。
```

训练目标：

```latex
trajectory_log_prob = sum(step_action_token_log_probs)
advantage = return - moving_average_baseline
loss = - advantage.detach() * trajectory_log_prob
```

要求：

```latex
1. 只对 assistant 生成的 action token 计算 log-prob，不对 prompt token 计算 loss；
2. invalid JSON/action 也必须保留 raw generation 和 log_prob，不能从 policy-gradient batch 中静默丢弃；
3. submit、max_steps、invalid termination 或 guardrail terminal 后停止 rollout；
4. 只更新 LoRA/QLoRA adapter 参数；
5. dry-run 必须验证至少一个 adapter 参数发生变化；
6. train_reinforce.py 必须输出 reward curve、loss curve、baseline curve 和 validation private pass curve。
```

关键实现约束：rollout 阶段保存的 log_prob 只能作为审计、debug 和日志；REINFORCE update 阶段必须使用当前 policy 对保存的 prompt token ids + generated action token ids 重新 forward，重新 gather assistant action token 上的 log-prob，并用这个带梯度的 `trajectory_log_prob` 参与 loss。不得直接使用 rollout 阶段 detached 的 log_prob 反向传播。

```latex
rollout 保存：prompt_ids、action_ids、attention_mask、raw_output、parsed_action；
update 重新计算：current_policy(prompt_ids + action_ids) -> action_token_log_probs；
loss 使用：fresh trajectory_log_prob with grad；
rollout log_prob 用途：debug / audit / metrics only。
```

### 2.6 Synthetic Benchmark split 去重与 leakage audit
除了 task_id 唯一，还必须进行 bug-level 去重，避免 train/test 近重复导致 hidden pass 被高估。

每个任务必须计算：

```latex
bug_signature = repo + function_name + bug_type + hash(gold_patch.old_text) + hash(gold_patch.new_text)
```

强制检查：

```latex
1. train/validation/test 之间 bug_signature 不得重复；
2. split 间 gold_patch.old_text/new_text pair 不得完全相同；
3. split 间 bug_description 不得完全相同；
4. split 间 failing public assertion literal 不得完全相同；
5. dataset_report.md 必须输出重复率、近重复样例和每个 split 的 signature 分布。
```

`validate_tasks.py` 若发现 hard leakage，必须失败退出；near-duplicate 第一版只输出 top-k warning，不阻塞生成流程，但必须写入 `reports/dataset_report.md`，供人工复核。

---

## Phase 0：项目脚手架与工程规范
### 🎯 任务目标与范围
建立一个可维护的 Python 工程骨架，让后续所有模块都能通过统一命令测试、格式化、静态检查和运行脚本。此阶段不实现业务逻辑，只完成工程基础设施。

范围控制：Phase 0 只服务后续 benchmark、env、tool、evaluation 闭环。不要因为工程规范引入过多非必要复杂度；pytest 和 ruff 是必须项，mypy、pre-commit、CI-like checks 均为可选项，不得阻塞核心闭环。

### 🧑‍💻 人类（我）的任务
你需要决定：

```latex
1. 项目目录名：MiniRepair-RL；
2. 使用 uv 还是 pip；建议 uv；
3. Python 版本：建议 3.11；
4. 是否创建 GitHub 远程仓库；
5. 是否启用 pre-commit；第一版可暂缓。
```

### 🤖 Claude Code 的执行任务
Claude Code 需要：

```latex
1. 创建标准目录结构；
2. 创建 pyproject.toml；
3. 配置 pytest、ruff；mypy 可作为可选配置；
4. 创建基础 README；
5. 创建 .gitignore；
6. 创建最小 smoke test；
7. 确保 python -m pytest 可运行；
8. 提交初始 Git commit 建议。
```

### 💻 Claude Code 命令行指令
在 Claude Code 中直接输入：

```bash
我将从零实现 MiniRepair-RL。请先创建 Python 3.11 项目脚手架：
- 使用 src-layout 或 package-layout，包名为 minirepair
- 创建 pyproject.toml，配置 pytest、ruff；mypy 可选，不应阻塞核心闭环
- 创建 README.md、.gitignore、configs/、scripts/、reports/、logs/
- 创建 minirepair/env、minirepair/data、minirepair/agents、minirepair/training、minirepair/evaluation
- 创建一个最小 smoke test，确保 pytest 能通过
- 完成后运行 ruff check 和 pytest
- 最后给出建议的 git commit message
```

如果 Claude Code 已创建文件，可继续要求它运行：

```bash
请检查当前仓库结构是否符合上述要求，读取 pyproject.toml 和 tests/，运行：
python -m pytest
ruff check .
如果失败，请修复到全部通过。
```

### ✅ 验收标准 (Definition of Done)
```latex
1. 仓库目录存在且结构清晰；
2. pyproject.toml 能安装基础依赖；
3. python -m pytest 通过；
4. ruff check . 通过；
5. README.md 至少包含项目目标、安装、测试命令；
6. minirepair 包可以被 import；
7. 有一个合理的初始 git commit message。
```

---

## Phase 1：Benchmark 最小闭环
### 🎯 任务目标与范围
构建最小 synthetic bug benchmark。目标不是一次生成完整 130 个任务，而是先创建 2 个 mini repo template 和 20 个 seed tasks，验证 public/private 测试、metadata schema、gold patch 和离线质量验证样例能跑通。

注意：正式 benchmark 语义中，`tests_hidden/` 严格只允许出现在 test split，并且只能在 `EvalMode.FINAL_TEST` 下用于 frozen final evaluation。Phase 1 的 seed tasks 若需要额外边界样例辅助验证任务质量，必须使用 `tests_quality_holdout/`，不得使用 `tests_hidden/`；这些质量验证样例只能由 `validate_tasks.py` 在 `EvalMode.DATASET_VALIDATION` 下读取，不能进入训练、模型选择、prompt、SFT 构造、reward ablation 调参或 Agent observation。train/validation split 主要依赖 private tests 作为训练 reward 与模型选择信号；test split 的 hidden tests 只用于最终报告。

### 🧑‍💻 人类（我）的任务
你需要确认：

```latex
1. 第一版只做两个 repo：string_utils、validators；
2. 第一版只做两类 bug：boundary/edge-case、string/validation processing；
3. 每个任务只允许单文件小 patch；
4. task metadata 使用 JSON 或 JSONL；建议 JSONL；
5. public/private/hidden/quality_holdout tests 的命名约定：train/validation 不得有 tests_hidden/；test 才有 tests_hidden/；seed 阶段额外验证样例使用 tests_quality_holdout/。
```

建议目录约定：

```latex
benchmarks/
  templates/
    string_utils/
    validators/
  tasks/
    seed/
      task_0001/
        metadata.json
        repo/
          src/
          tests/
          tests_private/
          tests_quality_holdout/   # seed 阶段仅用于离线质量验证；正式 train/validation 不得出现 tests_hidden/
```

### 🤖 Claude Code 的执行任务
Claude Code 需要：

```latex
1. 定义 TaskMetadata pydantic schema；
2. 创建 string_utils 和 validators 两个 repo template；
3. 为每个 repo 编写正常源码和测试；
4. 创建 20 个带 bug 的 seed tasks；
5. 每个 task 包含 metadata、buggy repo、gold patch；
6. 编写 dataset validation 脚本；
7. 验证每个 task 初始 public tests 至少有失败；
8. 验证应用 gold patch 后 public/private/hidden tests 全通过。
```

### 💻 Claude Code 命令行指令
```bash
请实现 MiniRepair-RL 的最小 benchmark vertical slice：
1. 在 minirepair/data/task_schema.py 中定义 TaskMetadata 和 GoldPatch schema；
2. 创建 benchmarks/templates/string_utils 和 benchmarks/templates/validators；
3. 每个 template 包含 src/、tests/、tests_private/；如需额外离线质量验证样例，使用 tests_quality_holdout/，不得在 train/validation 使用 tests_hidden/；
4. 创建 20 个 seed tasks，覆盖 boundary 和 string/validation bug；
5. 每个 task 有 metadata.json、repo/、gold_patch；
6. 编写 scripts/validate_tasks.py，检查：
   - metadata schema 合法；
   - buggy repo 的 public tests 至少有一个失败；
   - train/validation/seed 默认不得包含 tests_hidden/；
   - 应用 gold patch 后 public/private tests 全通过；
   - seed 阶段如存在 tests_quality_holdout/，仅在 EvalMode.DATASET_VALIDATION 下验证；
   - test split 的 tests_hidden/ 只允许在 EvalMode.FINAL_TEST 或 EvalMode.DATASET_VALIDATION 下访问；
7. 运行 validate_tasks.py 和 pytest。
请优先实现可运行闭环，不要过度抽象。
```

补充修复指令：

```bash
请读取 scripts/validate_tasks.py 的输出，逐个修复失败的 task。不要跳过失败任务。修复后重新运行：
python scripts/validate_tasks.py --tasks benchmarks/tasks/seed
python -m pytest
```

### ✅ 验收标准 (Definition of Done)
```latex
1. 至少 20 个 seed tasks；
2. 每个 task 有 metadata.json；
3. 每个 seed task 有 public/private tests；如需额外离线质量验证样例，使用 tests_quality_holdout/；
4. seed/train/validation 不得包含 tests_hidden/；
5. buggy 状态下 public tests 至少失败 1 个；
6. 应用 gold patch 后 public/private tests 全通过；
7. validate_tasks.py 能批量验证全部 seed tasks；
8. task schema 有单元测试；
9. benchmark 文件不依赖本机绝对路径。
```

---

## Phase 2：工具层、沙箱与 Guardrails
### 🎯 任务目标与范围
实现 CodeRepairEnv 的底层工具：`read_file`、`search_code`、`edit_file`、`run_tests`、`submit`。此阶段重点是工具行为必须可控、可复现、可记录，并且严格防止 reward hacking。

### 🧑‍💻 人类（我）的任务
你需要确认工具约束：

```latex
1. read_file 单次最大返回 200 行；
2. search_code 只搜索 src/；
3. edit_file 使用 old_text/new_text 精确 search-replace；
4. old_text 必须在目标文件中精确出现一次；
5. 每次 edit 只能修改一个文件；
6. 每次 edit 最多修改 5 行；
7. 每个 episode 最多 2 次 edit；
8. 禁止修改 tests/、tests_private/、tests_hidden/、tests_quality_holdout/；
9. 禁止修改 pytest.ini、pyproject.toml、conftest.py；
10. run_tests 只允许运行 public tests；
11. private/hidden tests 只允许 evaluator/reward 使用，不能进入 agent observation。
12. guardrails 必须检测高价值 reward hacking 行为，包括跳过测试、删除断言、修改测试配置、大规模删除代码等；对“硬编码 public test case / 固定返回值只满足 public tests”第一版采用 heuristic 标记 potential reward hacking，不要求 100% 静态识别。
```

### 🤖 Claude Code 的执行任务
Claude Code 需要：

```latex
1. 实现 sandbox.py：临时复制 task repo，隔离执行；
2. 实现 tools.py：五个工具的核心逻辑；
3. 实现 guardrails.py：检测违规编辑；
4. 实现 action_schema.py：结构化 JSON action schema；
5. 为每个工具编写单元测试；
6. 确保工具返回结构化 observation；
7. 确保所有工具调用可被记录和 replay。
```

### 💻 Claude Code 命令行指令
```bash
请实现工具层和 sandbox：
- minirepair/env/sandbox.py：负责将 task repo 复制到临时工作目录，执行 pytest，并清理资源
- minirepair/env/action_schema.py：定义 Action、ToolName、ToolArguments，支持 JSON parse 和 validation error
- minirepair/env/guardrails.py：实现禁止修改测试、配置、删除 assert、pytest.skip/xfail、超大修改等规则
- minirepair/env/tools.py：实现 read_file、search_code、edit_file、run_tests、submit

工具约束：
- read_file 只能读 repo 内文件，默认最多 200 行
- search_code 只搜索 src/
- edit_file 必须使用单文件 search-replace patch interface
- old_text 必须在目标文件中精确出现一次
- 每次 edit_file 只能修改一个文件
- 每次 edit_file 最多修改 5 行
- 每个 episode 最多允许 2 次 edit_file 调用，超出后必须返回明确失败 observation
- run_tests 只能运行 public tests
- submit 本阶段只返回 submitted 状态，不做 reward

请为每个工具写 pytest 单元测试，并运行 pytest。失败请修复。
```

针对安全性补充：

```bash
请专门补充 guardrail tests：
1. 修改 tests/ 应失败；
2. 修改 tests_private/ 应失败；
3. 修改 tests_hidden/ 应失败；
4. 修改 tests_quality_holdout/ 应失败；
5. 修改 pyproject.toml/conftest.py/pytest.ini 应失败；
5. 修改 requirements.txt、pyproject.toml、setup.cfg 等依赖或测试配置应失败；
6. old_text 出现 0 次或多次应失败；
7. new_text 包含 pytest.skip 或 pytest.xfail 应失败；
8. 删除 assert 应失败；
9. 单次修改超过 5 行应失败；
10. 明显硬编码 public test case 输入/输出可先用 heuristic 标记为 potential reward hacking，不要求第一版完全自动阻断；
11. 大规模删除函数体、直接 return 固定 public case 答案、针对 public traceback 中具体 literal 写 if 分支，应被记录为 potential reward hacking attempt；只有高置信度违规才直接阻断。
运行 pytest，直到全部通过。
```

### ✅ 验收标准 (Definition of Done)
```latex
1. 五个工具全部实现；
2. 工具输入输出有明确 schema；
3. run_tests 不会暴露 private/hidden tests；
4. edit_file guardrails 全部生效；
5. sandbox 不污染原始 task repo；
6. 工具层单元测试覆盖正常路径和失败路径；
7. pytest 全部通过；
8. ruff check 全部通过。
9. edit_file 明确禁止 multi-file patch，每次调用只能修改 action.arguments.path 指定的单个文件；
10. 超过 edit budget 时，环境必须返回结构化失败 observation，而不是静默忽略。
11. guardrails 对明显 public-test hardcoding 有 heuristic 标记测试覆盖，不要求完全识别所有 hardcoding；
12. 所有 guardrail violation 都会写入 trajectory info，便于后续 failure analysis。
```

---

## Phase 3：CodeRepairEnv 最小可交互环境
### 🎯 任务目标与范围
将工具层封装为有限步长 MDP 环境。Agent 每次提交结构化 action，环境返回 observation、reward、done、info。此阶段先不接模型，只支持手写 action sequence 和 replay。



本阶段需要明确区分 Env 内部状态与 Agent 可见状态：

1. Env 内部可以维护 task metadata、working tree、budgets、tool history、last observation、modified files summary、guardrail status 和 termination state；
2. Agent 每一步只能通过 `render_state()` 看到可见 MDP state；
3. `render_state()` 必须只包含调试所需信息，不得泄漏 private tests、hidden tests、gold_patch、changed_files oracle、private reward 或 hidden evaluation result；
4. `step(action_json)` 返回的 observation 同样必须遵守 no-leakage 约束。

### 🧑‍💻 人类（我）的任务
你需要确认环境参数：

```latex
Max episode steps = 6
Max run_tests calls = 2
Max edit_file calls = 2
Consecutive invalid actions before termination = 3
```

### 🤖 Claude Code 的执行任务
Claude Code 需要：

```latex
1. 实现 CodeRepairEnv.reset(task_id)；
2. 实现 CodeRepairEnv.step(action_json)；
3. 实现 state rendering；
4. 记录 tool history；
5. 记录 modified files summary；
6. 实现 step budget、edit budget、test budget；
7. 实现 termination conditions；
8. 实现 trajectory JSONL logging；
9. 实现 replay_trajectory.py。
```

### 💻 Claude Code 命令行指令
```bash
请实现 CodeRepairEnv：
- 文件：minirepair/env/code_repair_env.py
- 支持 reset(task_path)、step(action_json)、render_state()
- 每个 step 接收 JSON 字符串或 dict action
- 内部调用 tools.py
- 维护：step_count、edit_count、test_count、invalid_count、tool_history、last_observation、done、termination_reason
- 限制：max_steps=6、max_edits=2、max_tests=2、连续 3 次 invalid action 终止
- 记录 JSONL trajectory，包含 task_id、step、action、observation、reward、done、info
- 实现 scripts/replay_trajectory.py，能重放一条 trajectory

请写测试：
1. 手写 gold action sequence 可修复至少 5 个 seed tasks；
2. 超过 max_steps 会终止；
3. 超过 max_edits 会失败或终止；
4. 连续 invalid action 会终止；
5. trajectory 可以 replay。
运行 pytest 和 ruff check。
```

手动验收指令：

```bash
请创建 scripts/run_manual_episode.py，内置一个 seed task 的 gold action sequence，并打印每一步 observation。运行：
python scripts/run_manual_episode.py --task benchmarks/tasks/seed/task_0001
确认最终 submit 后 public/private/hidden 检查逻辑不向 agent observation 泄漏 private/hidden 内容。
```

### ✅ 验收标准 (Definition of Done)
```latex
1. CodeRepairEnv 可以 reset 和 step；
2. 手写 action sequence 可以修复至少 5 个任务；
3. max_steps/max_edits/max_tests 生效；
4. invalid action termination 生效；
5. trajectory JSONL 信息完整；
6. replay 能复现工具调用结果；
7. agent observation 不包含 private/hidden test 内容；
8. pytest、ruff 全部通过。
```

---

## Phase 4：完整 Benchmark 生成与验证
### 🎯 任务目标与范围
从 20 个 seed tasks 扩展到固定规模 benchmark：Train 80、Validation 20、Test 30，总计 130 个任务。此阶段重点是 dataset 质量、split 隔离和可复现生成。

边界要求：`tests_hidden/` 严格只生成在 test split，并且只能用于 test split 的最终 frozen evaluation，不能用于训练、模型选择、prompt 构造、SFT target 构造或 reward ablation 调参。train/validation split 不得包含 `tests_hidden/`。如需离线质量验证样例，使用 `tests_quality_holdout/`，且只能由 `validate_tasks.py` 在 `EvalMode.DATASET_VALIDATION` 下读取。代码实现上必须要求所有 private/hidden/quality_holdout evaluation 显式传入 `EvalMode`，并在非允许模式下直接拒绝读取。

### 🧑‍💻 人类（我）的任务
你需要确认：

```latex
1. 是否允许 template-based controlled mutation；建议允许；
2. 是否将 generated benchmark commit 进 Git；建议 commit metadata 和小规模任务；
3. random seed；建议 42；
4. 是否保持两类 bug 大致均衡；建议是。
```

### 🤖 Claude Code 的执行任务
Claude Code 需要：

```latex
1. 实现 bug_generator.py；
2. 实现 split.py；
3. 实现 scripts/generate_tasks.py；
4. 生成 train/validation/test 三个 split；
5. 确保 tests_hidden/ 只存在于 test split，train/validation 不得生成 tests_hidden/；
6. 检查 split 间 bug instance 与 bug_signature 不重合；
8. 检查 bug type 分布；
9. 执行 split leakage audit，检查 gold_patch pair、bug_description、failing public assertion literal 是否跨 split 重复；
10. 批量验证所有 gold patches。
```

### 💻 Claude Code 命令行指令
```bash
请将 benchmark 从 seed tasks 扩展为完整 130-task dataset：
- Train: 80
- Validation: 20
- Test: 30
- 两个 repo：string_utils、validators
- 两类 bug：boundary、string_validation
- 使用 deterministic random seed=42

请实现：
- minirepair/data/bug_generator.py
- minirepair/data/split.py
- scripts/generate_tasks.py
- scripts/validate_tasks.py 的 full benchmark 支持

生成目录：
benchmarks/train/
benchmarks/validation/
benchmarks/test/

生成后运行：
python scripts/generate_tasks.py --seed 42 --output benchmarks
python scripts/validate_tasks.py --tasks benchmarks/train benchmarks/validation benchmarks/test
python -m pytest
```

质量检查补充：

```bash
请为 benchmark 添加 dataset quality report：
- 每个 split 的 task 数量
- 每个 repo 的分布
- 每个 bug_type 的分布
- public/private 测试数量；test split 额外统计 hidden 测试数量；如存在 tests_quality_holdout/，单独统计且不得纳入主实验
- gold patch 验证通过率
- bug_signature 跨 split 重复率
- gold_patch old_text/new_text pair 跨 split 重复率
- bug_description 跨 split 重复率
- near-duplicate warning 样例
输出到 reports/dataset_report.md。
```

### ✅ 验收标准 (Definition of Done)
```latex
1. train=80、validation=20、test=30；
2. task_id 全局唯一；
3. bug_type 分布大致均衡；
4. 每个任务 buggy public tests 至少失败 1 个；
5. gold patch 后 train/validation 的 public/private tests 全通过，test 的 public/private/hidden tests 全通过；
6. full benchmark validation 通过；
7. reports/dataset_report.md 自动生成；
8. 生成过程 deterministic。
```

---

## Phase 5：ReAct Baseline
### 🎯 任务目标与范围
实现不训练模型的 ReAct baseline，用 prompt + tool-use loop 跑完整 validation/test split，建立 no-training baseline 和早期 failure trajectory 集合。

### 🧑‍💻 人类（我）的任务
你需要提供：

```latex
1. 正式主实验的 ReAct、SFT、RL 必须使用同一 base model：Qwen2.5-Coder-1.5B-Instruct，以保证公平对比；
2. Claude Code 当前环境、Anthropic API、OpenAI-compatible API 或其他商业模型只作为 smoke test / engineering reference baseline，默认不得进入主结果表；如需展示，只能进入 reference appendix，并明确标注不可与 Qwen SFT/RL 直接比较；
3. 是否允许人工手动跑小样本；建议先支持 mock/local，再接真实 LLM；
4. API key 不要写入仓库；使用环境变量。
```

### 🤖 Claude Code 的执行任务
Claude Code 需要：

```latex
1. 实现 action_parser.py；
2. 实现 react_agent.py；
3. 设计 ReAct prompt；
4. 确保正式对比实验中的 ReAct policy 与 SFT/RL 使用同一 base model；外部 API baseline 只作为补充参考；
5. 将 LLM 输出解析为结构化 JSON action；
5. 接入 CodeRepairEnv loop；
6. 实现 evaluator.py 和 metrics.py；
7. 输出 public pass、validation private pass / test hidden pass、invalid action/edit、avg steps 等指标；
8. 保存 trajectories 和 metrics CSV。
```

### 💻 Claude Code 命令行指令
```bash
请实现 ReAct baseline：
- minirepair/agents/action_parser.py：从 LLM 输出中提取 JSON action，处理 markdown code block 和非法 JSON
- minirepair/agents/react_agent.py：构造 prompt，调用 policy backend，执行 env loop
- minirepair/evaluation/metrics.py：计算 public pass、validation private pass / test hidden pass、invalid action rate、invalid edit rate、regression rate、avg steps、avg tool calls、submit-before-test rate、guardrail violation rate
- minirepair/evaluation/evaluator.py：批量跑 split，保存 metrics.csv 和 trajectories/*.jsonl
- scripts/run_react.py：CLI 入口

先实现一个 MockPolicy，用 gold patch 或固定策略跑 smoke test，再预留真实 LLM backend 接口。使用 gold_patch 的 MockPolicy 仅允许用于 smoke test 和 pipeline validation。其指标必须从 reports/main_results.md、reports/react_baseline.md、reports/reward_ablation.md 和任何正式对比表中排除。建议在 metrics 中写入 `excluded_from_main_results=true`，并让 summarize_metrics.py 默认拒绝纳入 mock/gold/oracle policy 结果，除非显式使用 `--include-smoke-tests`。
运行：
python scripts/run_react.py --split validation --max-tasks 5 --policy mock
python -m pytest
```

真实 LLM 接入提示：

```bash
请为 react_agent.py 添加一个可插拔 LLMPolicy 接口：
- 不在仓库中保存 API key
- 从环境变量读取模型配置
- 每次 LLM 输出必须经过 action_parser
- 解析失败时将 invalid action 交给环境处理，而不是直接崩溃
- 保存原始 LLM 输出到 trajectory log 的 raw_output 字段
```

完整 baseline 指令：

```bash
请运行或准备以下命令，并确保输出 reports/react_baseline.md：
python scripts/run_react.py --split validation --policy qwen_base --model Qwen/Qwen2.5-Coder-1.5B-Instruct --output logs/react_validation
python scripts/run_react.py --split test --policy qwen_base --model Qwen/Qwen2.5-Coder-1.5B-Instruct --output logs/react_test
python scripts/summarize_metrics.py --inputs logs/react_validation logs/react_test --output reports/react_baseline.md
```

### ✅ 验收标准 (Definition of Done)
```latex
1. MockPolicy 能跑通 validation 小样本；
2. ReAct agent 不因非法 JSON 崩溃；
3. 每条 trajectory 保存 raw_output、parsed_action、observation、done、info；
4. validation/test split 可批量运行；
5. 输出 metrics.csv；
6. reports/react_baseline.md 包含主指标；
7. 至少收集 20 条失败 trajectory；
8. private/hidden tests 不进入 prompt 或 observation。
```

---

## Phase 6：SFT Gold Trajectory 与 LoRA/QLoRA SFT
### 🎯 任务目标与范围
构造 supervised fine-tuning 数据集，让模型学习合法 JSON action schema 和基本工具顺序。SFT 的目标不是直接追求最优 hidden pass，而是降低 invalid action/edit、premature submit 等工具使用问题。

Oracle 边界：SFT 可以使用 train split 的 gold_patch 离线构造 target action，但 gold_patch 不得出现在 prompt、Agent 可见状态、runtime observation 或 validation/test 推理过程中。

SFT 数据边界：

1. SFT supervised targets 只能从 project train split 的 gold_patch 构造；
2. 不允许从 project validation split 或 project test split 构造 gold supervised targets；
3. 如果 SFT 训练需要 dev/eval loss，应从 project train split 内部再划分 sft_train / sft_dev；
4. project validation split 只用于训练过程中的 policy-level evaluation、checkpoint selection 和 ReAct/SFT/RL 对比；
5. project test split 只用于最终 frozen evaluation；
6. validation/test split 的 gold_patch 只允许用于 benchmark quality validation，不得进入 SFT dataset、prompt、runtime observation 或 model target。

### 🧑‍💻 人类（我）的任务
你需要确认：

```latex
1. Base model：Qwen2.5-Coder-1.5B-Instruct；
2. Fine-tuning：LoRA 或 QLoRA；
3. 训练设备：本地 GPU、Colab、AutoDL、云服务器；
4. 是否先只生成 SFT dataset，不立即训练；建议先生成并检查数据。
```

### 🤖 Claude Code 的执行任务
Claude Code 需要：

```latex
1. 实现 trajectory_builder.py；
2. 从 gold_patch 构造 gold trajectories；
3. 加入有限扰动：search first、read distractor、不同 thought 模板；
4. 转换为 chat/SFT 格式；
5. 实现 scripts/build_sft_dataset.py；
6. 实现 training/train_sft.py；
7. 添加 configs/sft.yaml；
8. 支持小样本 dry-run；
9. 实现 SFT policy inference adapter。
```

### 💻 Claude Code 命令行指令
```bash
请实现 SFT 数据构造：
- minirepair/data/trajectory_builder.py
- scripts/build_sft_dataset.py

要求：
1. 只能从 project train split 的 metadata.gold_patch 构造 supervised gold trajectories；
2. 不允许从 project validation split 或 project test split 构造 supervised targets；
3. 如需 SFT eval loss，从 project train split 内部划分 sft_train / sft_dev；
4. 基础轨迹：read_file -> edit_file -> run_tests -> submit；
5. 加入有限扰动：部分任务 search_code -> read_file，部分任务 read 一个 distractor file；
6. thought 使用多个模板，避免完全重复；
7. 输出 JSONL，每条包含 messages 或 prompt/completion，适配 TRL SFTTrainer；
8. 确保 private/hidden tests 不进入 prompt；
9. gold_patch 只允许离线用于 train split 的 supervised target actions，不得进入 prompt、runtime observation、validation/test inference context，也不得用于 validation/test 的训练或模型选择。

运行：
python scripts/build_sft_dataset.py \
  --source-split train \
  --dev-fraction 0.1 \
  --seed 42 \
  --output-train data/sft_train.jsonl \
  --output-dev data/sft_dev.jsonl

python scripts/inspect_sft_dataset.py --input data/sft_train.jsonl --num-samples 5
python scripts/inspect_sft_dataset.py --input data/sft_dev.jsonl --num-samples 5
python -m pytest
```

训练实现指令：

```bash
请实现 LoRA/QLoRA SFT 训练入口：
- configs/sft.yaml
- minirepair/training/train_sft.py
- scripts/train_sft.py

要求：
1. 使用 transformers、peft、trl；
2. 支持 model_name、dataset_path、output_dir、batch_size、learning_rate、epochs、lora_r、lora_alpha；
3. 支持 --dry-run，仅加载 8 条样本跑 1-2 step；
4. 保存 adapter 到 outputs/sft_adapter；
5. 训练完成后可用 SFTPolicy 在 env 中生成 action。

请不要硬编码 API key 或本机路径。
```

SFT 评估指令：

```bash
请不要新建独立的 scripts/run_sft_policy.py。请实现 SFTPolicy，并统一通过 scripts/evaluate.py 调用，避免后续命令入口分裂。

命令：
python scripts/train_sft.py --config configs/sft.yaml --dry-run
python scripts/evaluate.py   --method sft   --split validation   --eval-mode validation_selection   --adapter outputs/sft_adapter   --max-tasks 5   --output logs/eval/sft_validation_smoke
```

如果保留 `scripts/run_sft_policy.py`，它只能作为 `scripts/evaluate.py --method sft` 的薄 wrapper，不得另写一套评估逻辑。

### ✅ 验收标准 (Definition of Done)
```latex
1. sft_train.jsonl 和 sft_dev.jsonl 生成成功；
2. sft_train/sft_dev 均只来自 project train split；
3. build_sft_dataset.py 会拒绝 validation/test source split；
4. SFT prompt 不泄漏 private/hidden tests；
5. gold action target 格式合法；
6. dry-run training 可完成；
7. SFTPolicy 可以在 env 中生成 action；
8. SFT 相比 ReAct 至少在小样本上降低 invalid JSON/action；
9. 输出 ReAct vs SFT 初版 metrics；
10. 训练脚本参数化，不依赖绝对路径。
```

---

## Phase 7：Reward 与 REINFORCE RL Fine-tuning
### 🎯 任务目标与范围
在 SFT policy 基础上实现轻量级 RL fine-tuning。第一版只实现 REINFORCE with moving-average baseline，并对比 sparse reward 与 dense reward。

本阶段对 Claude Code 来说复杂度最高，必须拆成五个可独立验收的子阶段，不允许一次性要求 Claude Code 同时实现 reward、rollout、log-prob、policy update 和完整训练循环。

### 7.0 Phase 7 拆分执行原则
```latex
Phase 7A: reward.py + sparse/dense reward 单元测试；
Phase 7B: rollout collection，不训练，只保存完整 trajectory；
Phase 7C: action token log-prob reconstruction，并写 shape/unit tests；
Phase 7D: 单 batch REINFORCE update，验证 LoRA adapter 参数发生变化；
Phase 7E: 接入完整 sparse/dense training loop、validation private evaluation 和 reward ablation。
```

禁止事项：

```latex
1. 不得用 heuristic reranking 冒充 RL；
2. 不得只记录 reward 而不反传 log-prob；
3. 不得丢弃 invalid JSON/action 的 trajectory；
4. 不得更新 base model 全参；
5. 不得读取 hidden tests 做训练、模型选择或 reward ablation 调参；
6. 不得使用 gold_patch similarity、changed_files oracle 或 patch minimality 作为 reward。
```

### 🧑‍💻 人类（我）的任务
你需要确认：

```latex
1. 第一版不用 PPO/GRPO/RLOO；
2. 每个 task rollout 2-4 条 trajectories；
3. sparse reward 和 dense reward 都需要跑；
4. validation private tests 只用于模型选择；
5. test hidden tests 只用于 frozen pipeline 的最终评估，不用于训练、模型选择、reward ablation 调参或 prompt 构造；
6. 若 GPU 资源不足，先完成 dry-run 和小规模 RL，保证 execution-based RL 闭环真实存在。
```

### 🤖 Claude Code 的执行任务
Claude Code 需要按以下顺序实现：

```latex
1. Phase 7A：实现 reward.py、sparse reward、dense reward 和 reward tests；
2. Phase 7B：实现 rollout.py，只采样和保存 trajectory，不更新模型；
3. Phase 7C：实现 token-level action log-prob 计算，只对 assistant action tokens 计入 loss；
4. Phase 7D：实现单 batch REINFORCE update，验证至少一个 LoRA adapter 参数变化；
5. Phase 7E：实现 train_reinforce.py、sparse/dense config、validation tracking、adapter save、curve export；
6. 输出 reward ablation 初版结果。
```

### 💻 Claude Code 命令行指令
#### Phase 7A：Reward 系统
```bash
请先只实现 reward 系统，不要实现训练循环：
- minirepair/env/reward.py
- tests/test_reward.py

Sparse reward：
+1.0 terminal private tests 全部通过
0.0 否则
-1.0 severe guardrail violation terminal

Dense reward：
+1.0 terminal private tests 全部通过
+0.5 public tests 全部通过
+0.2 原本失败的 public tests 变为通过
+0.1 valid edit
-0.2 引入 public regression
-0.05 每次额外 tool call
-0.3 invalid action 或 JSON 格式错误
-0.5 invalid edit
-1.0 severe guardrail violation terminal

要求：
- Agent observation 不能看到 private reward 细节；
- reward info 可以写入 training log；
- hidden tests 不参与训练、模型选择或 reward ablation 调参；
- patch minimality 不进入 reward，只能作为 evaluation metric；
- 不允许使用 gold patch similarity reward；
- 不允许使用 changed_files、gold_patch、private/hidden test 内容构造 reward shaping；
- dense reward 只能来自 public test feedback、private terminal reward、valid/invalid action/edit、regression、step penalty、guardrail penalty；
- 所有 private/hidden test access 必须显式接收 EvalMode。

运行：
python -m pytest tests/test_reward.py
ruff check .
```

#### Phase 7B：Rollout collection
```bash
请实现 rollout collection，但暂时不要做 policy update：
- minirepair/training/rollout.py
- tests/test_rollout.py

要求：
1. 从 SFT adapter 或 mock trainable policy 初始化；
2. 每个 task 可采样 2-4 条 trajectories；
3. 每一步保存 prompt、raw model output、parsed action、observation、reward、done、info；
4. invalid JSON/action 也必须保留 raw generation，不能静默丢弃；
5. submit、max_steps、invalid termination 或 guardrail terminal 后停止 rollout；
6. rollout log 不得包含 private/hidden traceback、测试名、gold_patch 或 changed_files oracle。

运行：
python -m pytest tests/test_rollout.py
python -m pytest
```

#### Phase 7C：Action token log-prob reconstruction
```bash
请实现 action token log-prob 计算：
- minirepair/training/logprob.py 或集成到 rollout.py
- tests/test_logprob.py

要求：
1. rollout 阶段保存 prompt token ids、generated action token ids、attention mask；
2. 只对 assistant 生成的 action token 计算 log-prob，不对 prompt token 计算 loss；
3. 每一步保存 per-step action token log_prob，用于 debug / audit / metrics；
4. 每条 trajectory 保存 trajectory_sum_log_prob，用于日志审计；
5. update 阶段必须用当前 policy 重新 forward 计算带梯度 action-token log-prob，不得直接复用 rollout 阶段 detached log_prob 反传；
6. 测试覆盖 batch size=1、多步 trajectory、invalid JSON raw output 三种情况；
7. 测试至少检查 tensor shape、requires_grad、mask 位置和 log_prob 非空。

运行：
python -m pytest tests/test_logprob.py
```

#### Phase 7D：单 batch REINFORCE update
```bash
请实现最小 REINFORCE 单 batch update：
- minirepair/training/train_reinforce.py
- tests/test_reinforce_update.py

训练目标：
# update 阶段重新 forward 当前 policy，得到带梯度的 action-token log-prob
trajectory_log_prob = sum(fresh_step_action_token_log_probs)
advantage = return - moving_average_baseline
loss = - advantage.detach() * trajectory_log_prob

要求：
1. 使用完整 trajectory return；
2. 使用 moving-average baseline 计算 advantage；
3. 只更新 LoRA/QLoRA adapter 参数；
4. dry-run 必须验证至少一个 adapter 参数发生变化；
5. invalid JSON/action trajectory 不得从 batch 中丢弃；
6. 输出 loss、return、baseline、advantage；
7. 单元测试必须确认用于 loss 的 trajectory_log_prob 连接当前 policy 计算图，而不是 rollout 日志中的 detached log_prob。

运行：
python -m pytest tests/test_reinforce_update.py
```

#### Phase 7E：完整 sparse/dense RL training loop
```bash
请在前四个子阶段通过后，再实现完整 REINFORCE 训练闭环：
- scripts/train_rl_sparse.py
- scripts/train_rl_dense.py
- configs/rl_sparse.yaml
- configs/rl_dense.yaml

要求：
1. 从 SFT adapter 初始化 policy；
2. 每个 task rollout 2-4 条 trajectories；
3. 使用完整 trajectory return；
4. 使用 moving-average baseline 计算 advantage；
5. trajectory_log_prob = sum(step_action_token_log_probs)；
6. loss = - advantage.detach() * trajectory_log_prob；
7. 只更新 LoRA/QLoRA adapter 参数；
8. 记录 reward、loss、baseline、episode length、invalid action/edit、public/private pass；
9. 每轮在 validation set 上评估 private_pass_rate，不读取 hidden tests；
10. 支持 --dry-run，仅跑 2 个 task、1 个 update；
11. 保存 adapter 到 outputs/rl_sparse_adapter 和 outputs/rl_dense_adapter；
12. 输出 reward curve、loss curve、baseline curve 和 validation private pass curve。

先运行 dry-run：
python scripts/train_rl_sparse.py --config configs/rl_sparse.yaml --dry-run
python scripts/train_rl_dense.py --config configs/rl_dense.yaml --dry-run
python -m pytest
```

Ablation 指令：

```bash
请实现 reward ablation 汇总脚本：
- scripts/compare_rewards.py

输入 sparse/dense 的 validation 与 test metrics logs，输出 reports/reward_ablation.md，包含：
Reward | Val Private Pass | Test Hidden Pass | Invalid Action | Invalid Edit | Avg Steps

命令格式必须支持：
python scripts/compare_rewards.py \
  --validation-inputs logs/eval/rl_sparse_validation logs/eval/rl_dense_validation \
  --test-inputs logs/eval/rl_sparse_test logs/eval/rl_dense_test \
  --output reports/reward_ablation.md
```

### ✅ 验收标准 (Definition of Done)
```latex
1. sparse/dense reward 单元测试通过；
2. rollout collection 可保存完整 trajectory；
3. action token log-prob reconstruction 有 shape/mask/requires_grad 测试；
4. 单 batch REINFORCE update 能验证至少一个 LoRA adapter 参数变化；
5. moving-average baseline 正常更新；
6. validation metrics 每轮保存；
7. sparse 和 dense 两条训练命令都能运行；
8. reward curve、loss curve、baseline curve 和 validation private pass curve 可导出；
9. hidden tests 不参与训练和模型选择；
10. reports/reward_ablation.md 可同时读取 validation 与 test logs 生成；
11. reward.py 没有 gold patch similarity、changed_files oracle、patch minimality reward；
12. patch minimality 只在 evaluation/metrics.py 中统计。
```

---

## Phase 8：统一 Evaluation、Metrics 与 Failure Analysis
### 🎯 任务目标与范围
建立最终评估体系，统一比较 ReAct、SFT、SFT+RL，并输出 main results、reward ablation、failure taxonomy 和 case studies。

评估边界：validation private tests 可用于训练过程中的模型选择；test hidden tests 只用于最终 frozen evaluation，不用于选择 checkpoint、调 reward、改 prompt 或筛选结果。

### 🧑‍💻 人类（我）的任务
你需要决定：

```latex
1. 最终报告中是否展示全部失败轨迹；建议只展示代表性 case；
2. 是否将 logs/trajectories commit；建议小样本 commit，大量日志放 release/artifact；
3. 简历 bullet 使用哪些真实指标；必须等最终结果出来再填。
```

### 🤖 Claude Code 的执行任务
Claude Code 需要：

```latex
1. 统一 evaluator CLI；
2. 统一 metrics schema；
3. 生成 main results table；
4. 生成 reward ablation table；
5. 实现 failure_taxonomy.py；
6. 自动抽样 failure cases；
7. 输出 reports/failure_analysis.md；
8. 输出可复现命令列表。
```

### 💻 Claude Code 命令行指令
```bash
请完善最终 evaluation 模块：
- minirepair/evaluation/evaluator.py
- minirepair/evaluation/metrics.py
- minirepair/evaluation/failure_taxonomy.py
- minirepair/evaluation/reports.py
- scripts/evaluate.py
- scripts/summarize_metrics.py

`scripts/evaluate.py` 必须显式接收 `--eval-mode`，合法值为 `validation_selection` 或 `final_test`。validation split 必须搭配 `--eval-mode validation_selection`，test split 的最终评估必须搭配 `--eval-mode final_test`。不得在 `split == test` 时隐式读取 hidden tests；必须由显式 eval mode 解锁。

统一支持以下 method：
- react
- sft
- rl_sparse
- rl_dense

指标包括：
1. public pass rate
2. validation private pass rate 或 test hidden pass rate
3. validation public-private gap 或 test public-hidden gap
4. invalid action rate
5. invalid edit rate
6. regression rate
7. average steps
8. average tool calls
9. submit-before-test rate
10. repeated test call rate
11. guardrail violation rate
12. average read/search/edit/test action counts
13. patch minimality metric

repeated test call rate 定义：
- 同一 episode 中，在没有新的 valid edit 发生的情况下重复调用 run_tests 的比例。
- 用于衡量 Agent 是否浪费测试预算或陷入无效调试循环。

patch minimality metric 定义：
- 只作为 evaluation metric；
- 可统计 modified lines、modified files、edit calls；
- 不得进入 reward；
- 不得使用 gold patch similarity 作为 reward。

运行命令示例：
python scripts/evaluate.py --method react --split validation --eval-mode validation_selection --policy qwen_base --model Qwen/Qwen2.5-Coder-1.5B-Instruct --output logs/eval/react_validation
python scripts/evaluate.py --method react --split test --eval-mode final_test --policy qwen_base --model Qwen/Qwen2.5-Coder-1.5B-Instruct --output logs/eval/react_test
python scripts/evaluate.py --method sft --split validation --eval-mode validation_selection --adapter outputs/sft_adapter --output logs/eval/sft_validation
python scripts/evaluate.py --method sft --split test --eval-mode final_test --adapter outputs/sft_adapter --output logs/eval/sft_test
python scripts/evaluate.py --method rl_sparse --split validation --eval-mode validation_selection --adapter outputs/rl_sparse_adapter --output logs/eval/rl_sparse_validation
python scripts/evaluate.py --method rl_sparse --split test --eval-mode final_test --adapter outputs/rl_sparse_adapter --output logs/eval/rl_sparse_test
python scripts/evaluate.py --method rl_dense --split validation --eval-mode validation_selection --adapter outputs/rl_dense_adapter --output logs/eval/rl_dense_validation
python scripts/evaluate.py --method rl_dense --split test --eval-mode final_test --adapter outputs/rl_dense_adapter --output logs/eval/rl_dense_test
python scripts/summarize_metrics.py \
  --inputs \
    logs/eval/react_test \
    logs/eval/sft_test \
    logs/eval/rl_sparse_test \
    logs/eval/rl_dense_test \
  --require-main-comparable \
  --output reports/main_results.md
```

Failure analysis 指令：

```bash
请实现 failure analysis：
- 自动读取 failed trajectories
- 按以下 taxonomy 分类：
  1. Localization error
  2. Context misunderstanding
  3. Invalid action
  4. Invalid edit
  5. Semantic patch error
  6. Regression error
  7. Premature submit
  8. Tool misuse
  9. Reward hacking attempt
- 每类输出 1-2 个 case study，包含 task_id、method、trajectory 摘要、失败原因、可能修复方向
- 输出 reports/failure_analysis.md
```

### ✅ 验收标准 (Definition of Done)
```latex
1. 所有 method 用同一 evaluator 评估；
2. main_results.md 自动生成；
3. reward_ablation.md 自动生成；
4. failure_analysis.md 最小版本至少包含 5 类失败分析；完整目标覆盖原方案 9 类 taxonomy，每类 1–2 个 case study；
5. 每个 case study 可追溯到 trajectory JSONL；
6. hidden test 只在 test split final_eval mode 最终评估使用；validation split 使用 private_pass_rate 做模型选择；
7. 指标计算有单元测试；
8. 最终表格可直接放进 README 或报告。
9. metrics.py 包含 repeated_test_call_rate 的单元测试；
10. metrics.py 包含 patch minimality 统计，但该指标不参与 reward。
```

---

## Phase 9：README、技术报告与简历材料
### 🎯 任务目标与范围
将项目整理为简历和面试可展示的研究型工程项目。重点不是包装，而是保证别人能够复现 setup、baseline、SFT、RL 和 evaluation。

### 🧑‍💻 人类（我）的任务
你需要提供：

```latex
1. 最终实验结果数值；
2. GPU/训练资源说明；
3. 是否公开模型 adapter；
4. 简历目标岗位方向：Agent / RL / Code Agent / SWE AI；
5. 你希望 README 偏工程还是偏研究。
```

### 🤖 Claude Code 的执行任务
Claude Code 需要：

```latex
1. 完善 README；
2. 写 technical report；
3. 写 setup/run/train/evaluate 命令；
4. 写 limitations；
5. 写 reproducibility checklist；
6. 写 resume bullets；
7. 检查所有命令是否与实际脚本一致。
```

### 💻 Claude Code 命令行指令
```bash
请生成最终项目文档：
1. README.md：
   - 项目简介
   - 系统架构图 ASCII
   - 安装命令
   - 生成 benchmark
   - 运行 ReAct baseline
   - 构建 SFT 数据
   - 训练 SFT
   - 训练 RL sparse/dense
   - 最终评估
   - 主要结果表格
   - failure analysis 摘要
   - limitations

2. reports/technical_report.md：
   - problem formulation
   - MDP design
   - tool interface
   - benchmark design
   - reward design
   - training setup
   - experiments
   - results
   - failure analysis
   - threats to validity

3. reports/resume_bullets.md：
   - 无结果版本
   - 有结果版本
   - 如果 RL 未提升 hidden pass 的备选版本

请确保 README 中所有命令都真实存在。完成后运行：
python -m pytest
ruff check .
```

最终一致性检查指令：

```bash
请做一次 release readiness audit：
- 检查 README 中每条命令是否对应真实脚本
- 检查 configs 是否都能被脚本加载
- 检查 reports 是否引用了真实 metrics 文件
- 检查 private/hidden tests 是否不会进入 prompt、SFT input 或 agent observation
- 检查 .gitignore 是否不会误提交大模型权重和大日志
- 输出 reports/release_checklist.md
```

### ✅ 验收标准 (Definition of Done)
```latex
1. README 可指导新用户完整跑通项目；
2. technical_report.md 结构完整；
3. resume_bullets.md 有可替换指标位置；
4. release_checklist.md 完成；
5. 所有 README 命令与脚本一致；
6. pytest 和 ruff 通过；
7. 没有提交 API key、大模型权重、大日志；
8. 项目能清楚回答：RL 是否改善了 code repair agent 的多步调试行为？
```

---

## 10. 推荐 Claude Code 工作流
### 10.1 每个阶段的标准交互模式
每个阶段都建议使用以下固定节奏：

```bash
请先读取相关文件，给出本阶段实现计划，不要马上大规模改动。
```

然后：

```bash
请按刚才计划实现，优先小步提交，每完成一个模块就运行对应测试。
```

最后：

```bash
请运行完整测试和静态检查，总结改动、剩余风险，并给出建议 git commit message。
```

### 10.2 让 Claude Code 自检的通用指令
```bash
请审查你刚才的实现，重点检查：
1. 是否存在 private/hidden test leakage；
2. 是否有硬编码绝对路径；
3. 是否有未测试的失败路径；
4. 是否有 reward hacking 漏洞；
5. 是否有 silent failure；
6. 是否有过度抽象导致的复杂度。
发现问题请直接修复，并补充测试。
```

### 10.3 让 Claude Code 做 Git 提交建议
```bash
请总结当前 diff，按 Conventional Commits 格式给出一个 commit message，并列出本次提交包含的主要文件和测试结果。不要自动提交，先让我确认。
```

### 10.4 让 Claude Code 定位失败测试
```bash
请读取 pytest 失败输出，先解释根因，再最小化修复。不要通过删除测试或放宽验收标准来绕过失败。修复后重新运行失败测试和完整 pytest。
```

---

## 11. 全链路最终命令清单
以下命令应在项目完成后全部可运行。正式主表中的 ReAct/SFT/RL 必须使用同一 base model。外部 API baseline 只能作为 reference baseline，默认不得进入主结果表。

```bash
# 1. 安装
uv sync
# 或
pip install -e '.[dev]'

# 2. 质量检查
ruff check .
python -m pytest

# 3. 生成 benchmark
python scripts/generate_tasks.py --seed 42 --output benchmarks
python scripts/validate_tasks.py --tasks benchmarks/train benchmarks/validation benchmarks/test

# 4. 跑 ReAct baseline
# 正式主实验必须显式使用 Qwen base model，避免 evaluator 默认走 MockPolicy 或外部 API。
python scripts/run_react.py \
  --split validation \
  --policy qwen_base \
  --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --output logs/react_validation

python scripts/run_react.py \
  --split test \
  --policy qwen_base \
  --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --output logs/react_test

# 5. 构建 SFT 数据
# 注意：SFT supervised targets 只能来自 project train split；validation/test split 不得用于构造 SFT target。
# 如需 dev/eval loss，应从 train split 内部再划分 sft_train / sft_dev。
python scripts/build_sft_dataset.py \
  --source-split train \
  --dev-fraction 0.1 \
  --seed 42 \
  --output-train data/sft_train.jsonl \
  --output-dev data/sft_dev.jsonl

# 6. 训练 SFT
python scripts/train_sft.py --config configs/sft.yaml

# 7. 评估 SFT
python scripts/evaluate.py --method sft --split validation --eval-mode validation_selection --adapter outputs/sft_adapter --output logs/eval/sft_validation
python scripts/evaluate.py --method sft --split test --eval-mode final_test --adapter outputs/sft_adapter --output logs/eval/sft_test

# 8. 训练 RL sparse/dense
python scripts/train_rl_sparse.py --config configs/rl_sparse.yaml
python scripts/train_rl_dense.py --config configs/rl_dense.yaml

# 9. 最终评估
# validation logs 用于 private_pass_rate / checkpoint selection 口径；test logs 用于 frozen hidden final evaluation。
python scripts/evaluate.py \
  --method react \
  --split validation \
  --eval-mode validation_selection \
  --policy qwen_base \
  --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --output logs/eval/react_validation

python scripts/evaluate.py \
  --method react \
  --split test \
  --eval-mode final_test \
  --policy qwen_base \
  --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --output logs/eval/react_test

python scripts/evaluate.py --method sft --split validation --eval-mode validation_selection --adapter outputs/sft_adapter --output logs/eval/sft_validation
python scripts/evaluate.py --method sft --split test --eval-mode final_test --adapter outputs/sft_adapter --output logs/eval/sft_test
python scripts/evaluate.py --method rl_sparse --split validation --eval-mode validation_selection --adapter outputs/rl_sparse_adapter --output logs/eval/rl_sparse_validation
python scripts/evaluate.py --method rl_sparse --split test --eval-mode final_test --adapter outputs/rl_sparse_adapter --output logs/eval/rl_sparse_test
python scripts/evaluate.py --method rl_dense --split validation --eval-mode validation_selection --adapter outputs/rl_dense_adapter --output logs/eval/rl_dense_validation
python scripts/evaluate.py --method rl_dense --split test --eval-mode final_test --adapter outputs/rl_dense_adapter --output logs/eval/rl_dense_test

# 10. 生成报告
python scripts/summarize_metrics.py \
  --inputs \
    logs/eval/react_test \
    logs/eval/sft_test \
    logs/eval/rl_sparse_test \
    logs/eval/rl_dense_test \
  --require-main-comparable \
  --output reports/main_results.md

python scripts/compare_rewards.py \
  --validation-inputs logs/eval/rl_sparse_validation logs/eval/rl_dense_validation \
  --test-inputs logs/eval/rl_sparse_test logs/eval/rl_dense_test \
  --output reports/reward_ablation.md

python scripts/analyze_failures.py \
  --inputs \
    logs/eval/react_validation logs/eval/react_test \
    logs/eval/sft_validation logs/eval/sft_test \
    logs/eval/rl_sparse_validation logs/eval/rl_sparse_test \
    logs/eval/rl_dense_validation logs/eval/rl_dense_test \
  --output reports/failure_analysis.md
```

---

## 12. 阶段优先级建议
如果时间有限，优先完成：

```latex
P0: Phase 0-3
必须完成。没有环境和工具闭环，项目不成立。若时间紧，优先保证可运行闭环，不要被 mypy、typer、pre-commit、复杂 CI 或过强 hardcoding 检测拖慢。

P1: Phase 4-5
必须完成。没有 benchmark 和 ReAct baseline，无法评估。

P2: Phase 6
强烈建议完成。SFT 是连接 Agent 工程和模型训练的关键。

P3: Phase 7
尽量完成。必须至少完成 Phase 7A-7D，确保 reward、rollout、token log-prob 和单 batch policy-gradient update 真实可运行；若资源不足，Phase 7E 可先小规模 dry-run，但不能用伪 RL 或 heuristic reranking 替代。

P4: Phase 8-9
必须至少完成 README、main results 和 failure analysis。简历项目最怕只有代码没有结论。
```

---

## 13. 最小可展示版本标准
如果无法完成完整 5 周版本，最小可展示版本应至少包含：

```latex
1. 20-50 个 synthetic tasks；
2. public/private/hidden tests；
3. CodeRepairEnv；
4. read/search/edit/test/submit 工具；
5. constrained edit guardrails；
6. ReAct baseline；
7. SFT dataset builder；
8. 至少 SFT dry-run；
9. evaluator metrics；
10. failure analysis；
11. README 可复现命令。
```

不建议只做 UI 或 demo。这个项目的核心卖点是 **test-verifiable Agent RL environment + evaluation discipline**。

---

## 14. 最终验收总表
| 模块 | 必须验收项 |
| --- | --- |
| Benchmark | 130 tasks，gold patch 验证通过，split 隔离 |
| Env | reset/step/replay 可用，budget 和 termination 生效 |
| Tools | read/search/edit/test/submit 全部测试覆盖 |
| Guardrails | 禁止修改测试、配置、skip/xfail、删除 assert |
| ReAct | validation/test 可跑，非法 JSON 不崩溃 |
| SFT | dataset 合法，dry-run training 可跑，SFTPolicy 可评估 |
| RL | sparse/dense reward，REINFORCE dry-run 可更新参数 |
| Eval | main results、reward ablation、failure analysis 自动生成 |
| Docs | README、technical report、resume bullets、release checklist |
| Quality | pytest、ruff 通过，无密钥、无大权重、无路径硬编码 |


---

## 15. 建议的首个 Claude Code Prompt
你可以从下面这段开始：

```bash
你是我的资深 AI coding assistant。我们要从零实现 MiniRepair-RL，一个 test-verifiable code repair agent RL environment。请严格按阶段小步实现，不要一次性写完所有模块。

当前目标是 Phase 0：项目脚手架与工程规范。
请先创建 Python 3.11 项目结构、pyproject.toml、README.md、.gitignore、minirepair 包目录、tests 目录和一个 smoke test。配置 pytest、ruff；mypy 可选。完成后运行 pytest 和 ruff check，并给出建议 git commit message。

注意：后续项目会实现 structured tool actions、CodeRepairEnv、synthetic bug benchmark、ReAct baseline、SFT、REINFORCE RL。请现在只做脚手架，不要提前实现业务逻辑。
```

---

## 16. 项目核心判断标准
最终这个项目是否成功，不取决于 RL 是否一定显著提升 hidden pass rate，而取决于是否能严谨回答：

```latex
1. ReAct、SFT、SFT+RL 在同一 benchmark 上表现如何？
2. SFT 是否降低 invalid action/edit？
3. RL 是否改善多步调试行为？
4. dense reward 是否比 sparse reward 更稳定？
5. public pass 与 hidden pass 是否存在泛化差距？
6. 失败主要来自定位、语义 patch、工具误用，还是 reward hacking？
```

只要这些问题能用可复现实验和 trajectory evidence 回答，MiniRepair-RL 就是一个有说服力的 Agent/RL/Code Agent 项目。

