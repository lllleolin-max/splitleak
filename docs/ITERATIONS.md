# Real review cycles

Initial implementation has been built and wheel-installed on Windows / Python 3.14.3; 13 tests, the SDK workflow and contrast all passed. This initial build is not a review cycle. Subsequent entries record actual failing review probes against committed predecessor states, substantive corrections and observed verification. No passing initial feature chunk is counted as an iteration.

Raw environment paths stay in ignored local logs; public evidence preserves commands/results without local usernames.

## Cycle 1: typed SDK failures for malformed destinations

Before: `a1001616ed27435904eec6d9a7447174446b9f9f` (initial commit).

Self-review traced validation order for structured malformed input. Actual command `python probes/review_1.py` against the installed initial wheel exited 1: `AssertionError: expected InputError, got TypeError`. `allowed_splits=[{}]` reached set construction before string validation. This broke the documented SDK error contract and could crash an integrator expecting InputError.

Correction: validate destination element types before deduplication; add four malformed structured/bool/mixed destination cases to SDK tests. Rebuilt/reinstalled the normal wheel, reran the same probe (exit 0, `review_1: PASS (4 malformed SDK destinations rejected as InputError)`), and ran the complete suite (14 tests, OK). Full after SHA is recorded in the final evidence index because a commit cannot contain its own SHA.
