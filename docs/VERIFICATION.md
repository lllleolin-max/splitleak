# Executed verification, 2026-10-03

Environment: Windows, CPython 3.14.3. Core final source SHA `81025cc37faa6e7f2a56e3f3db22016126da7800`; later additions are evidence/replay/verification tooling and documentation. Independent external portfolio evaluation is still pending; this file awards no scores.

Build: `python -m build --wheel` used an isolated backend with setuptools 84.0.0 satisfying the declared >=77.0.3 minimum. Normal wheel `splitleak-0.1.0-py3-none-any.whl` was installed into a **fresh** `.venv-final` using pip; source was not editable. Import asserted `site-packages`. The builder environment had build 1.6.1, packaging 26.3, pyproject-hooks 1.3.3; the runtime wheel has no third-party requirements.

| Actual command (activated fresh wheel environment) | Observed result |
|---|---|
| `python -m unittest discover -s tests -v` | 19 tests, OK; independent oracle checks 45 generated constrained problems plus all fixtures |
| `python examples/workflow.py` | OPTIMAL, cost 2, retained test 1/train 5, residual edges 0, path hops 3 |
| `python benchmarks/contrast.py` | nine same-constraint comparisons + six threshold settings; results in tracked RESULTS.json |
| `python tools/verify_release.py` | actual console audit→explain→plan→apply→check; five exit codes 0, source unchanged, cost 2, retained 6, residual edges 0 |
| `python probes/review_1.py` | PASS: 4 malformed destination inputs rejected as InputError |
| `python probes/review_2.py` | PASS: decimal equality allowed, extreme finite evidence serialized |
| `python probes/review_3.py` | PASS: repeated JSON policy key rejected, CLI exit 2 |
| `python tools/replay_iterations.py` (builder environment with build installed) | three exact Git archive predecessor failures / successor passes; full archived after suites 14/15/19 tests OK |

The tests cover duplicate IDs; bool/nonfinite/numeric errors; zero threshold; null/missing/partial times; scoped half-open time and strict embargo equality; contradictory pins; retention, move/delete/cost restrictions; ties/permutations; partial group deletion; deleted bridge isolation; changed source commitment/claimed cost/forged witness; state exhaustion with and without an inspected feasible upper bound; strict JSON ambiguity/bytes/depth; and source preservation/refused overwrite. Independent implementation is not independent authorship; root assigns external review.

Checked-in Actions configuration runs Ubuntu/Windows × Python 3.11/3.14 with normal wheel install, tests, actual SDK/console workflows and contrast. Remote Actions have **not** run locally; root verifies them after publication. This machine has no local Python 3.11 installation, so local results apply to Python 3.14.3 only.

Limitations: 200 rows, ten splits, <=100000 characters per text, quadratic pair evidence and exponential exact assignment search, bounded at 100000 visited states by default. Declared lexical/subject/scoped temporal relations only; no conceptual-leakage completeness, anonymity, signer authenticity, causal proof, real customers/revenue or ML-gain claim. Original-component isolation is intentionally conservative and may make pinned holdouts infeasible.
