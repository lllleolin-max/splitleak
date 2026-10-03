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
