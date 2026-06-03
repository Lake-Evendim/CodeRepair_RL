# Resume Bullets — MiniRepair-RL

面向岗位方向：Agent / RL

---

## Version A: 无结果版

适用于项目尚未跑完全部实验、或需要提前投递简历的场景。

**MiniRepair-RL: RL for Code Repair Agents** | Python, PyTorch, LoRA, REINFORCE

- Designed and implemented a test-verifiable code repair agent environment as a finite-horizon MDP, with structured tool calling (read/search/edit/test/submit), constrained edit guardrails, and anti-reward-hacking detection
- Built a 130-task synthetic Python bug benchmark with public/private/hidden test splits, cross-split deduplication, and execution-based reward (sparse and dense variants)
- Implemented SFT warmup using LoRA on Qwen2.5-Coder via TRL, and REINFORCE RL fine-tuning with moving-average baseline and token-level log-prob policy gradient
- Developed a unified evaluation framework comparing ReAct, SFT, and SFT+RL methods with 13 metrics including hidden test pass rate, failure taxonomy, and patch minimality analysis

---

## Version B: 有结果版

适用于实验全部跑完、结果可展示的场景。

**MiniRepair-RL: RL for Code Repair Agents** | Python, PyTorch, LoRA, REINFORCE

- Built a complete code repair agent RL pipeline: 130-task benchmark, MDP environment with 5 structured tools and guardrails, SFT (LoRA) and REINFORCE RL training, unified evaluation
- SFT-trained Qwen2.5-Coder-1.5B achieved 70% hidden test pass rate (+10% over ReAct baseline), with 84.6% reduction in invalid edit attempts through gold trajectory imitation
- Implemented dense reward shaping with 7 signal types (edit quality, regression detection, progress tracking, efficiency penalties) and anti-reward-hacking guardrails blocking test manipulation and hardcoded returns
- Analyzed 73 failure episodes across 9-category taxonomy (localization, regression, tool misuse, etc.), identifying invalid edits (46.6%) and regression errors (27.4%) as primary failure modes

---

## Version C: 备选版（RL 未超过 SFT 时）

适用于 RL 未能显著超过 SFT 的情况，强调工程能力和评估严谨性。

**MiniRepair-RL: Test-Verifiable Code Repair Agent System** | Python, PyTorch, LoRA, REINFORCE

- Designed and end-to-end implemented a code repair agent system: synthetic benchmark (130 tasks, 140 bug variants), interactive MDP environment, SFT and RL training, and multi-metric evaluation
- Built constrained tool interface with 5 tools, edit guardrails (single-file, max 5 lines, forbidden path detection), and heuristic reward-hacking detection, ensuring training signal integrity
- SFT on Qwen2.5-Coder-1.5B (LoRA, 648 gold trajectories) achieved 70% hidden pass rate, 84.6% fewer invalid edits than zero-shot ReAct, demonstrating value of structured trajectory imitation
- Established evaluation discipline: EvalMode-enforced test isolation (public/private/hidden), 13 metric dimensions, 9-category failure taxonomy, and reproducible command pipeline — enabling rigorous comparison of ReAct, SFT, and RL methods

---

## 使用建议

1. **Version B 最强**，如果有真实数据支撑，优先使用
2. **Version A 适合早期投递**，可以先用，后续替换为 Version B
3. **Version C 适合 RL 不 work 的情况**，把卖点转移到工程严谨性和评估体系上
4. 根据 JD 调整侧重点：
   - 偏 Agent：强调工具接口设计、guardrails、多步调试行为分析
   - 偏 RL：强调 REINFORCE 实现、token-level log-prob、reward 设计、baseline 对比
   - 偏 SWE AI：强调 benchmark 设计、failure taxonomy、execution-based evaluation

## 指标替换位置

在 Version B 中，以下数值可根据最终实验结果替换：

| 占位符 | 当前值 | 含义 |
|--------|--------|------|
| `70%` | hidden test pass rate | 最终评估的核心指标 |
| `+10%` | 相对 ReAct 的提升 | SFT/RL 的增量价值 |
| `84.6%` | invalid edit 下降比例 | SFT 的工具使用质量提升 |
| `130` | 任务总数 | benchmark 规模 |
| `140` | bug 变体数 | 多样性 |
| `73` | 失败 episode 数 | 分析样本量 |
| `46.6%` / `27.4%` | 主要失败类别占比 | failure analysis 发现 |
