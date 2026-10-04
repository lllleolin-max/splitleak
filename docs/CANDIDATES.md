# Candidate union and executed costs

Version 0.2 changes which pairs reach the complete graph predicates, rather than
changing the predicates. Equal atomic groups, literal text and declared subjects
use buckets. Positive token-set Jaccard uses shared-token postings. Time supports
use a start-ordered sweep per scope with a heap of exact rational `end + embargo`
expirations. Their union is stored in bounded per-row bit masks and emitted in
canonical ID order. Every candidate is evaluated for every enabled reason, in
the original group/exact/subject/near/temporal-or-embargo order.

This preserves null handling, literal empty-text equality, Unicode casefolded
near matching, exact Fraction ratios, half-open overlap and strict embargo
boundaries. At threshold zero, every pair of nonempty token sets qualifies,
even disjoint sets. Empty token sets never qualify as near duplicates. Time
scopes stay separate. Indices are rebuilt within each call and do not survive
caller mutation or a different manifest. The original implementation already
computed token sets once; removing repeated tokenization is not a claimed gain.

Components, lexical shortest explanation paths, pinned holdouts, integer costs,
retention, repair objectives, budgets, UNKNOWN/INFEASIBLE and apply refusals are
unchanged. In particular, deleting a bridge does not undo original-component
isolation. The independent checker still derives all pairs separately and
checks complete proposals/manifests. Optimizer state caps and input limits stay
unchanged.

## Same-input synthetic measurement

The before wheel is raw-LF canonical `2a1c617426a96dc4f4fe7ddcd773ec364b3bd15f`
(0.1.0). The indexed wheel is
`0a776ea068e0defd395a13e8c288b19f3dc533f2`. Both were normal wheels installed
in separate fresh environments; `-I` imports their site packages. All seven
raw Git/archive/wheel/site module bytes were associated. Measurements ran on
Windows/Python 3.14.3 on the same shared workstation, with the same fixtures,
default planning budget and three untraced timing samples. Tracemalloc ran
separately, so its overhead is excluded from the timing median. Full numeric
records, load measurements, graph hashes and RSS scope are retained in
[CANDIDATE_RESULTS.json](../benchmarks/CANDIDATE_RESULTS.json).

| Input | Jaccard calculations before → after | Complete audit ms before → after | Whole plan + checker ms before → after | Audit traced peak B before → after |
| --- | ---: | ---: | ---: | ---: |
| 200 sparse rows, 50 private words each | 19,900 → 0 | 114.253 → 3.651 | 322.891 → 201.207 | 1,074,149 → 1,675,909 |
| 200 rows, one common token, no near edges | 19,900 → 19,900 | 117.242 → 105.655 | 318.353 → 316.951 | 1,083,213 → 1,703,785 |
| 200 rows, every reason, 19,900 edges | 19,900 → 19,900 | 225.458 → 144.646 | 233.893 → 160.579 | 26,828,431 → 26,882,205 |
| 200 disjoint rows, zero near threshold | 19,900 → 19,900 | 58.288 → 54.471 | 95.102 → 90.892 | 10,684,799 → 10,716,759 |
| Two sparse rows | 1 → 0 | 0.051 → 0.066 | 0.082 → 0.102 | 17,305 → 16,353 |
| One row | 0 → 0 | 0.050 → 0.040 | 0.066 → 0.057 | 6,637 → 9,405 |

Each calculation counts one actual intersection and one actual union through
an observing set subclass in the installed graph module. The benchmark calls
the ordinary SDK, without changing product source or importing a checkout.
Every complete graph's SHA256 is identical before/after and inputs are unchanged.

Audit includes load/digest, token/index construction and full report allocation.
Whole plan includes validation, graph construction, optimization and its final
independent checker, not just relation evaluation. All benchmark rows are pinned
to one split, so this measurement does not estimate expensive assignment search.
Dense output is unavoidably quadratic. Its observed timing improvement also
includes once-per-row exact temporal conversion and once-per-call threshold
conversion, rather than an asymptotic reduction in dense pair count.

Posting masks add memory: sparse/common-token audit peak allocation grew. Small
input timing can be worse. Windows process-lifetime peak RSS includes imports,
earlier cases and tracing; for sparse old/new it was 28,872,704/30,253,056 B and
for dense old/new 122,351,616/121,999,360 B. These are whole-process observations,
not graph-only allocation, a memory bound or a controlled production benchmark.
No universal latency, memory, ML quality or commercial benefit is claimed.

Run `python benchmarks/candidate_work.py --out new-result.json` after ordinary
installation to measure the same six inputs. Use a new filename; output is
create-only. Report environment and compare all cases, including small/dense
counterexamples, before using these local timings to choose a workflow.

## Compatibility and console checks

The new all-pairs reference uses independent pair enumeration/predicates,
component traversal and BFS. One hundred fixed seeds each contain 200 rows,
covering sparse/dense/null/empty/Unicode/casefold/time/zero-threshold inputs;
the same 100 inputs are shuffled. Full edges/reasons/ratios/order, components,
explanation paths, checker conflicts and repair reports match. Repair comparison
uses the same optimizer with reference edges; it is not a new independent
optimizer oracle. The unchanged earlier 96-case exhaustive assignment oracle
and original regression suite remain separate checks of optimization behavior.

The real console before wheel failed valid Unicode IDs under native GBK,
PYTHONUTF8=0, cp936 and cp1252; it exited 2. Its invalid-input stderr contained
an invalid JSON escape in legacy modes. UTF-8 mode succeeded. The indexed-only
wheel had identical CLI source bytes and the same failures. The substantive
console repair is `38c323b5f4c4db79c9a2ce2901306dd2c405a462`: ASCII-escaped
stdout/stderr machine JSON, with original UTF-8 `--out` report bytes unchanged.
The ten before/after cases are retained in
[before](evidence/update-unicode-before.json) and
[after](evidence/update-unicode-after.json). Original raw streams remain private.

The subsequent ordinary installation executed 80 sysconfig-console operations
across native, PYTHONUTF8=0/1, cp936 and cp1252: all five command workflows with
stdout and saved files, invalid partial time, overwrite refusal, UNKNOWN,
INFEASIBLE, forged-check rejection and apply refusal. Standard JSON parsing
consumed complete streams; no partial stdout or unexpected stderr remained.
Saved files matched SDK complete payloads, source/existing bytes were preserved,
and the old 0.1.0 installed checker accepted new proposals/manifests. The installed
SDK workflow, unchanged structural contrast and five-step release verifier pass.

These are author-run observations. Later independent review and remote matrix
CI are separate gates. CI keeps four OS/Python groups and the console-layout
step only on Windows/Python 3.14; its other three groups intentionally skip it.
