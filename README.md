# SplitLeak

Explain declared contamination chains in dataset splits, then propose and independently check a costed repair. For research/ML data stewards who must preserve expensive samples, frozen holdouts and atomic batches. Python 3.11+, MIT, standard-library runtime.

SplitLeak connects literal text duplicates, token-set Jaccard near duplicates, declared subjects, atomic groups, and scoped temporal support/embargo. An A→B→C path can constrain A and C even when they do not directly match. This is a **conservative isolation policy**, not proof of semantic equivalence. It does not discover all conceptual leakage.

## Install and run

From a clone on Windows PowerShell (replace the activation command on Linux with `source .venv/bin/activate`):

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install build
python -m build --wheel
python -m pip install dist/splitleak-0.1.0-py3-none-any.whl
python -m unittest discover -s tests -v
python examples/workflow.py
python benchmarks/contrast.py
```

The SDK workflow emits `OPTIMAL`, cost `2`, retained `{"test": 1, "train": 5}`, zero residual edges, and a three-hop A→D explanation. It writes inspectable audit, path, plan, manifest and checker JSON under ignored `output/sdk/`.

The console command uses new output files and refuses overwrite:

```text
splitleak audit examples/transitive.json --out audit.json
splitleak explain examples/transitive.json A D
splitleak plan examples/transitive.json --out proposal.json
splitleak apply examples/transitive.json proposal.json --out assignment.json
splitleak check examples/transitive.json assignment.json
```

`apply` writes an ID→split/null **assignment manifest**. Join it to your dataset locally; null means exclude that repair unit. It never rewrites source text or source splits. Keep artifacts in `output/` for repeated runs.

```python
import json
from splitleak import load, audit, explain, plan, check, apply

problem = load(json.load(open("examples/transitive.json", encoding="utf-8")))
report = audit(problem)
path = explain(problem, "A", "D")
proposal = plan(problem, max_states=100_000)
if proposal["assignment"] is not None and check(problem, proposal)["valid"]:
    manifest = apply(problem, proposal)
```

An `UNKNOWN` plan can carry an inspected feasible upper bound. Check it before using it; its cost is not certified minimal. `INFEASIBLE` means exhaustive search proved no allowed assignment. `OPTIMAL` means the declared integer-cost model was exhausted/pruned soundly; optimality is also tested against a separate small exhaustive oracle. The checker certifies feasibility, not the search proof.

## 中文：用途、使用与边界

SplitLeak 面向需要审查训练／验证／测试集的研究者和数据负责人。单独去重或按一列分组，可能遗漏近重复→同受试者→相邻时间支持形成的跨集链。它给出直接边类型、强度与传递路径，再在固定样本、整组、移动／删除成本和最低保留量约束内寻找修复。

上面的安装、SDK 示例和 CLI 命令可以直接运行。先 `audit` 看冲突，`explain` 看路径，再 `plan` 得到方案；`apply` 生成新的分配清单，最后 `check` 从原始输入独立重建关系并验证。合成示例保留六条数据，成本为二；这不表示模型指标提升或真实用户收益。

近重复关系本身通常不传递。将原始图的连通分量留在同一划分是明确的保守政策，删除中间桥也不解除两端的隔离要求。强政策可能与固定测试集冲突而无解；应先审查领域假设，不能为得到“干净”结果直接放松政策。缺失内容或时间会跳过相应关系，报告不能保证没有未声明的泄漏。

## Schema and relation semantics

See [docs/MODEL.md](docs/MODEL.md) for fields, boundary examples, cost objective and failure boundaries. Unknown fields, duplicate IDs, bool-as-number, negative/nonfinite costs, partial times and zero/reversed intervals are rejected. Missing/null content, subject and temporal support yield no relation for that field. Different temporal scopes never link merely because their timestamps coincide. Same subject can link through a separate configurable policy.

## Executed distinction and existing work

Current official documentation was inspected on **2026-10-03**:

- [scikit-learn grouped/time cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) already separates groups and supplies time-aware splits. These checks are established practice.
- [Deepchecks train/test validation](https://docs.deepchecks.com/stable/tabular/auto_checks/train_test_validation/index.html) documents train/test overlap and other validation checks.
- [Cleanlab Datalab issue types](https://docs.cleanlab.ai/stable/cleanlab/datalab/guide/issue_type_description.html) detects near duplicates using supplied features or a neighbor graph. Our small lexical Jaccard model has a narrower detection scope.

The engineering combination here is a visible mixed-relation path, a declared original-component isolation rule, bounded cost/retention repair and a separately implemented checker. No world-first or competitor-feature-absence claim is made. The executable **structural ablations** are not timing benchmarks of those products:

| Synthetic case | Row dedup: cost / residual edges | Single subject: cost / residual edges | Full graph: cost / residual edges |
|---|---|---|---|
| Mixed transitive chain, all 6 retained | 0 / 1 | 1 / 1 | 2 / 0 |
| Exact + subject pair, all 4 retained | 1 / 0 | 1 / 0 | 1 / 0 |
| Contradictory pinned chain | 0 / 1 | 0 / 1 | INFEASIBLE |

Every mode sees identical source data, policy, action permissions, costs and retention constraints. Baselines optimize their named subset and are evaluated by the **full** checker. Only their optimized relation subset changes; the full policy is never redefined to make a baseline succeed. Results include retained counts, component conflicts, states inspected and threshold sensitivity in [benchmarks/RESULTS.json](benchmarks/RESULTS.json).

## Maintenance and commercial rationale

An ML/research data steward could integrate the ID manifest into a dataset release review. Proposed value is fewer manual cross-relation investigations and auditable decisions about retaining costly annotations. If a team spends two hours per release tracing split disputes, saving even part of that review time may matter; this is an **unvalidated hypothesis**, with no measured time saving, customers, adoption, willingness to pay, revenue or ML improvement. Conservative over-grouping and exponential optimization may erase that benefit for large datasets.

Supported scope: at most 200 samples and ten splits, each content string at most 100,000 characters. Quadratic relation construction and exponential group search are for review slices and pilots, not million-row corpora. [Architecture](docs/ARCHITECTURE.md), [security](SECURITY.md), [contribution guide](CONTRIBUTING.md) and [real iteration evidence](docs/ITERATIONS.md) define operational boundaries. Checked-in CI targets Ubuntu/Windows × Python 3.11/3.14; local execution is distinguished from future remote CI.
