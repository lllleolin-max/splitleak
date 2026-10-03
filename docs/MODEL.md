# Declared model v1

Temporal numbers are interpreted using their decimal `str()` spelling, including floats received through the SDK. Arithmetic is exact in that decimal model: gap 0.3−0.1 equals embargo 0.2. Audit duration evidence uses `overlap_ratio`/`gap_ratio` strings so extreme finite endpoints never overflow to JSON infinity. The SDK does not recover precision already lost by a caller before passing a float.

Input is a JSON object with `samples`, optional `splits` (default train/validation/test), `policy`, `constraints`. See executable fixtures. SDK `load(dict)` returns an immutable validated `Problem`; all public functions also accept a dict.

| Sample field | Meaning / default |
|---|---|
| id, split | required nonempty strings; unique ID and declared split |
| content | optional string/null; literal exact comparison; no punctuation normalization |
| subject | optional nonempty string/null; declared shared source subject |
| group | optional nonempty string/null; **atomic repair unit**, always enforced |
| temporal_scope | optional nonempty string/null; a source stream/recording namespace |
| start, end | both finite numbers or both null/missing; `[start,end)` with end > start; scope required if supplied |
| allowed_splits | distinct list of declared split names; defaults to all; empty allows deletion only |
| move_cost | nonnegative integer units, charged once per moved row; default 1 |
| delete_cost | nonnegative integer units; null/missing forbids deletion |
| pinned | bool, default false; true fixes original split and forbids deletion |

Hard group membership requires all group rows assigned the **same split or all null**, even if they started in different splits. Grouping is separate from subject evidence; disabling the subject relation cannot disable atomic units.

Policy `exact`, `subject`, `temporal` default true. `near_threshold` defaults 0.8; null disables near relation. Tokenization is casefold + whitespace split + set; repeated tokens do not add weight. Nonempty token sets link if Jaccard >= threshold. Threshold 0 intentionally links every pair of nonempty token sets, even disjoint ones; missing/empty token sets do not create near edges. Empty strings can create exact edges. Strength is the direct similarity, never a probability of semantic equivalence.

Time uses a single caller-declared unit, not datetime or inferred chronology. Both scope values must be present and equal. `[0,2)` and `[2,4)` do not overlap. Positive embargo makes that pair link. With embargo 1, `[0,2)` and `[3,4)` **do not link**: equality is allowed; only gap < embargo links. Missing times skip support evidence, incomplete times fail. Zero-length intervals fail. Distinct scopes never link due to time alone. `embargo` defaults 0 and must be finite/nonnegative.

Every original graph connected component's retained rows must belong to one split. A→B→C does not imply A and C are semantically equivalent, but the isolation rule constrains them. Deleting B does not disconnect this policy. This prevents a cheap bridge deletion from erasing prior evidence, at the cost of conservative infeasibility. Re-auditing retained rows under a new policy is a new problem, not the same repair guarantee.

Constraints: `min_retained` maps splits to minimum row counts (default 0), `min_total` defaults 0, `max_moves` and `max_deletes` default sample count, `max_cost` defaults null (no extra cap). Counts include final destinations; original split sizes are not immutable. If you require frozen holdouts, pin their rows and restrict destinations. All costs use integers in caller-chosen common units; no probabilistic ML utility claim.

The objective is lexicographic `(sum action costs, deleted rows, moved rows, assignment vector)` with rows sorted by ID and destination names lexicographic (null sorts first). No scalar weighted tradeoff hides these ties. Exact source commitment includes normalized data, policy and constraints; it is not a signature, anonymity or proof of origin.

CLI exit codes: 0 success/OPTIMAL; 2 input/IO error; 3 proven INFEASIBLE; 4 UNKNOWN due to state bound; 5 rejected checker proposal. Audit exits 0 even if it reports conflicts, because it is an inspection operation. `--out` refuses an existing file. Apply requires a complete independently valid assignment and writes a fresh manifest.

Plan status certifies only optimizer search within this model. Checker certifies complete assignments, source commitment, action permissions, atomic units, original-component isolation, costs and retention. It reconstructs from source and ignores user-supplied edge/witness/check fields. It cannot prove all possible conceptual leakage absent. No embeddings, labels, causal inference, entity resolution or stratification are implemented.
