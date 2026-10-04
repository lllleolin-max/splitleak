# Real review cycles

Initial implementation has been built and wheel-installed on Windows / Python 3.14.3; 13 tests, the SDK workflow and contrast all passed. This initial build is not a review cycle. Subsequent entries record actual failing review probes against committed predecessor states, substantive corrections and observed verification. No passing initial feature chunk is counted as an iteration.

Raw environment paths stay in ignored local logs; public evidence preserves commands/results without local usernames.

## Cycle 1: typed SDK failures for malformed destinations

After: `0760e43c35e391ce6d158ed49f23169c96478028`.

Before: `a1001616ed27435904eec6d9a7447174446b9f9f` (initial commit).

Self-review traced validation order for structured malformed input. Actual command `python probes/review_1.py` against the installed initial wheel exited 1: `AssertionError: expected InputError, got TypeError`. `allowed_splits=[{}]` reached set construction before string validation. This broke the documented SDK error contract and could crash an integrator expecting InputError.

Correction: validate destination element types before deduplication; add four malformed structured/bool/mixed destination cases to SDK tests. Rebuilt/reinstalled the normal wheel, reran the same probe (exit 0, `review_1: PASS (4 malformed SDK destinations rejected as InputError)`), and ran the complete suite (14 tests, OK). Full after SHA is recorded in the final evidence index because a commit cannot contain its own SHA.

## Cycle 2: embargo equality and finite extreme spans

After: `31634e9321f875111373f64aa49a4aab8d4ee94f`.

Before: `0760e43c35e391ce6d158ed49f23169c96478028`.

Self-review tested decimal equality and finite arithmetic extremes. Actual `python probes/review_2.py` exited 1: `AssertionError: decimal gap == embargo incorrectly linked`. Separate serialization probe on two supports `[-1e308,1e308)` exited 1: `ValueError: Out of range float values are not JSON compliant: inf`, caused by the overlap span. These are supported boundary failures, not cosmetic errors.

Correction: graph temporal calculations use rational arithmetic from decimal spelling; checker separately uses Decimal with precision derived from input digit ranges. Duration evidence uses exact ratio strings. Integer finite validation avoids converting huge integers into floats. Oracle time arithmetic and regression coverage include decimal equality, extreme finite floats and 400-digit integer endpoints. Normal wheel rebuild/install, same probe and full suite verification are recorded in the final evidence index.

Observed after verification: `python probes/review_2.py` exited 0 (`decimal equality allowed; extreme finite evidence serializes`), complete suite 15 tests, OK.

## Cycle 3: reject ambiguous JSON declarations

Before: `31634e9321f875111373f64aa49a4aab8d4ee94f`.

Self-review checked machine-readable policy ambiguity at the CLI boundary. Actual `python probes/review_3.py` exited 1: `AssertionError: ambiguous JSON policy accepted`. The input declared the same subject policy twice, false then true; the ordinary decoder silently chose the last declaration. The same issue affected duplicate assignment keys and IDs within an object.

Correction: strict object-pairs decoding rejects repeated keys at every nesting level. Nonfinite constants, parser nesting exhaustion and files larger than 32 MiB get declared input errors. Add CLI workflow/source-preservation/overwrite and malformed JSON regression tests. Normal wheel rebuild/install, the same probe and full verification are recorded in the final evidence index.

Intermediate commit `bb72c4417da7e1fbd67cd2d2008b52ccebbfaf6f` passed the duplicate-policy probe but its full 18-test run had **one failure**: Python 3.14 decoded 2000 nested arrays without the expected RecursionError. The initial resource guard depended on parser behavior and therefore did not impose a stable depth bound. This result was not counted as a successful final verification. Follow-up adds a string/escape-aware pre-decoding depth limit of 64 with a bracket-in-text counterexample. The completed cycle's after SHA is in the final evidence index.

Final cycle-3 after: `81025cc37faa6e7f2a56e3f3db22016126da7800`; duplicate-policy probe exit 0, complete suite 19 tests, OK.

## Archive reproduction

The full immutable before/after SHAs are in [ITERATION_INDEX.json](ITERATION_INDEX.json). Run `python tools/replay_iterations.py` after installing `build`. It exports each exact commit with `git archive`, builds its normal wheel, installs into a fresh venv, asserts site-packages import, runs the **same final regression probe** against both states and requires the predecessor's exact failure message and successor exit 0. It also runs each after snapshot's own full tests. Raw logs and archive paths stay under ignored `.local/`.

Executed on Windows / Python 3.14.3 on 2026-10-03: all six probes returned expected exits (1 before / 0 after), with 14/15/19 archived after tests all passing. [ARCHIVE_REPLAY_RESULTS.json](ARCHIVE_REPLAY_RESULTS.json) is the actual redacted machine output, not a proposed result. The replay tool itself exited 0.

## 0.2.0 round 1 — measured exact candidate union

Baseline: `2a1c617426a96dc4f4fe7ddcd773ec364b3bd15f`. A fresh canonical LF
archive, ordinary wheel and isolated installed site matched all seven package
modules and passed the original 19 tests in 0.399 s. Remote README-only
`5d5bd1df076c80c8b8fa66ae3e8bcc2ad1c44a06` was fast-forwarded and retained.
No CodeGraph index existed. The old three actual failure/correction cycles were
replayed from normal archived wheels, with all six expected before/after exits
and after 14/15/19 suites passing. The earlier frozen independent 96-case
assignment oracle was run unchanged against the baseline installed wheel.

The old sparse 200-row/50-private-word case actually performed 19,900 Jaccard
calculations; this is a measured optimization opportunity, not a new violation
of the old contract. Tokens were already computed once. Implementation
`0a776ea068e0defd395a13e8c288b19f3dc533f2` unions group/exact/subject buckets,
shared-token postings and exact scoped time-sweep candidates with per-call masks.
Complete reasons and ID order remain. Threshold-zero disjoint nonempty sets,
empty exact matches, half-open overlap and strict embargo are preserved.

The new ordinary installation passed 24 tests in 59.559 s. One hundred seeded
200-row graphs and 100 shuffles matched full all-pairs evidence/components/path,
repair with reference edges and checker residuals: 714,954 emitted edges were
compared. This reference independently constructs the graph; the repair check
still uses the original optimizer, and does not replace the old independent
exhaustive assignment oracle. Same-input counts/time/allocation/RSS, including
small slower and common-token/dense cases, are retained in [CANDIDATES](CANDIDATES.md).

## 0.2.0 round 2 — real Unicode console failure and repair

Before: indexed `0a776ea068e0defd395a13e8c288b19f3dc533f2`, plus exact original
`2a1c617426a96dc4f4fe7ddcd773ec364b3bd15f` in its own ordinary environment.
Both CLI modules were byte-identical and the same ten actual-console cases
had identical results. Valid Unicode IDs exited 2 under native GBK, UTF8-off,
cp936 and cp1252; UTF8-on exited 0. Legacy invalid-input stderr included an
invalid JSON escape. The original stdout/stderr bytes and a failing
`--assert-success` run remain frozen; this is an actual supported workflow defect.

Correction: `38c323b5f4c4db79c9a2ce2901306dd2c405a462` serializes console/error
JSON with ASCII escapes, while saved `--out` reports preserve original UTF-8
bytes, payloads and exits. A meaningful installed-console regression covers
legacy and UTF-8 modes, source protection and invalid-output absence. The fresh
ordinary install passed 25 tests in 127.378 s; this shared-workstation duration
is not a timing comparison of algorithm performance. All ten focused cases
passed, followed by 80 complete command/error/refusal operations in five modes,
two old installed SDK checker consumers and three installed examples/verifiers.

## 0.2.0 round 3 — complete scope, bounded indices and final install

Review added nested interval expiry with time order differing from ID order,
and all exact/subject/temporal enabled combinations across null/zero/positive
near thresholds and strict embargo boundaries. It found no additional product
defect and does not manufacture a third bug. README, architecture, security,
changelog and the public offline SDK benchmark document local masks, complete
reason evaluation, immutable output semantics, dense quadratic output/checker,
index allocation and small-input costs. Both CI wheel filenames advance to
0.2.0; the four-group matrix and Windows/Python 3.14-only layout condition remain.

A table-copy helper initially lacked the new `docs/evidence` parent directory
and failed with FileNotFoundError after copying the numeric benchmark correctly.
Its original helper/failure attribution remains ignored; a separate helper
created the parent and copied only existing actual encoding tables. No product
code ran in that failed copy and no product fix is claimed for it.

The final clean SHA's canonical normal install binds all seven raw Git modules
to LF archive/wheel/site and executes the full 26-test suite, unchanged earlier
oracle, real sysconfig encoding workflows, old SDK consumers and examples.
Exact final SHA/receipts are generated separately at the freeze, since a commit
cannot contain its own identity. Prior reports, scores, history and failed
evidence remain unchanged. No independent score, production gain, customer,
revenue or remote CI result is inferred from these authored rounds.
