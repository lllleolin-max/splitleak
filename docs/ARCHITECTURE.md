# Architecture and complexity

`model.py` validates caller declarations and builds a canonical source commitment. `graph.py` computes pair evidence, union-find components, BFS evidence paths and audit reports. `repair.py` groups atomic units and traverses legal destinations with branch-and-bound cost/resource pruning. A component target is fixed by its first retained unit; deleting a unit never changes original connectivity.

Cost/resource counts accumulate monotonically, so a branch above an incumbent cost, action cap or cost cap cannot improve. Remaining-row bounds only eliminate branches unable to meet retention. Equal-cost branches remain searchable because deletion/move/assignment ties matter. The state counter bounds visited partial assignments; exhausting it produces UNKNOWN even when a feasible candidate exists. No uninspected heuristic solution is labelled optimal. An exhausted candidate is checked and called an upper bound.

The checker imports only the validated model. It separately implements pair predicates and graph reachability, counts actions and verifies the original source. Tests contain a second exhaustive oracle with row-level Cartesian assignment enumeration and Floyd-Warshall reachability, independent of the optimizer and checker. This is independent implementation, not external review or independent authorship. The oracle is explicitly limited to eight rows. Forty-five fixed-seed generated constrained problems and all synthetic fixtures compare actual objectives and assignments.

The graph builder's candidate union uses same-group/literal/subject buckets,
an inverted index of already computed casefolded token sets, and a time sweep
per declared scope. Positive Jaccard requires a shared token. At threshold zero
all nonempty token pairs are candidates, including disjoint sets. The time heap
expires a prior interval only when `end + embargo <= next_start`; overlap is
half-open and the embargo comparison remains strict. Every candidate receives
all enabled reasons in original order, rather than just its discovery reason.
Masks are local to one call and emitted in canonical ID-pair order. No index
crosses input snapshots or changes original-component isolation after deletion.

For n rows, total token occurrences T, c candidate pairs, e emitted edges, k
splits and g atomic units: tokenization first reads the full content. Posting
and bucket construction examines T tokens and n rows, using n-bit mask unions;
Python big-integer work grows with mask width, bounded here by 200 bits. Each
row emits its union's bits once; the scoped sweep sorts in O(n log n) and emits
active pairs. Each candidate's Jaccard calculation uses its complete token sets.
Candidate masks use O(n²) bits with the fixed 200-row cap; postings retain one
mask per distinct token. Full edge evidence uses O(e), with dense e = Θ(n²).
Token sets existed in the original builder; the optimization does not claim to
remove repeated token construction.

Explanation BFS is O(n + e), after graph construction. Search worst case is
O((k+1)^g × (n+g)); no polynomial scalability claim. The independent checker
remains O(n² × token work + n+e), and the small assignment oracle is exponential
in rows. Common-token or dense inputs retain quadratic pair work/output;
indexing can increase peak allocation and small-input latency. The unchanged
200-row/10-split/100000-character caps do not promise fast exact search. Choose
small review slices or strict state limits; inspect UNKNOWN candidates.

Reports expose stable sample IDs and relation evidence, not text, subjects or temporal namespace values. Time spans/gaps can still reveal information. IDs and commitment hashes are not anonymization; user-chosen IDs can contain identifying information, and low-entropy inputs can be guessed. Keep sensitive source documents local and review any artifacts before publication.
