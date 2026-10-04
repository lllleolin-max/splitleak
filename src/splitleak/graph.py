"""Declared pairwise evidence and conservative ORIGINAL-component isolation."""
from collections import deque
from fractions import Fraction
from heapq import heappop, heappush
from .model import problem


def _bits(mask):
    """Ascending indices from a bounded, per-call candidate bit mask."""
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def _candidate_pairs(p, tokens, times, threshold):
    # The validated input has at most 200 rows. Masks avoid retaining another
    # quadratic set of pair tuples alongside the unavoidable dense edge list.
    forward = [0] * len(p.samples)
    groups, exact, subjects, postings = {}, {}, {}, {}
    nonempty = 0
    for i, sample in enumerate(p.samples):
        bit, previous = 1 << i, 0
        for table, key in ((groups, sample.group),
                           (exact, sample.content if p.policy.exact else None),
                           (subjects, sample.subject if p.policy.subject else None)):
            if key is not None:
                previous |= table.get(key, 0)
                table[key] = table.get(key, 0) | bit
        if threshold is not None and tokens[sample.id]:
            if threshold == 0:
                # Disjoint NONEMPTY token sets have Jaccard zero and qualify.
                previous |= nonempty
                nonempty |= bit
            else:
                # Positive Jaccard necessarily shares a token. This does not
                # assume similarity is transitive or discard literal/group edges.
                for token in tokens[sample.id]:
                    previous |= postings.get(token, 0)
                    postings[token] = postings.get(token, 0) | bit
        for j in _bits(previous):
            forward[j] |= bit
    if p.policy.temporal:
        scopes = {}
        for i, sample in enumerate(p.samples):
            if sample.temporal_scope is not None and i in times:
                start, end = times[i]
                scopes.setdefault(sample.temporal_scope, []).append((start, end, i))
        embargo = Fraction(str(p.policy.embargo))
        for rows in scopes.values():
            active, expiry = 0, []
            for start, end, i in sorted(rows):
                # end + embargo == start is NOT eligible: half-open supports
                # and a strict embargo exclude equality (also when embargo=0).
                while expiry and expiry[0][0] <= start:
                    _, j = heappop(expiry)
                    active &= ~(1 << j)
                for j in _bits(active):
                    lo, hi = sorted((i, j))
                    forward[lo] |= 1 << hi
                active |= 1 << i
                heappush(expiry, (end + embargo, i))
    for i, mask in enumerate(forward):
        for j in _bits(mask):
            yield i, j


def relations(value):
    p = problem(value)
    threshold = None if p.policy.near_threshold is None else Fraction(str(p.policy.near_threshold))
    tokens = ({s.id: set(s.content.casefold().split()) if s.content is not None else set()
               for s in p.samples} if threshold is not None else {})
    times = {i: (Fraction(str(s.start)), Fraction(str(s.end)))
             for i, s in enumerate(p.samples)
             if p.policy.temporal and s.temporal_scope is not None and s.start is not None}
    embargo = Fraction(str(p.policy.embargo)) if p.policy.temporal else None
    edges = []
    for i, j in _candidate_pairs(p, tokens, times, threshold):
        a, b = p.samples[i], p.samples[j]
        reasons = []
        if a.group is not None and a.group == b.group:
            reasons.append({"kind": "group", "strength": 1, "meaning": "atomic repair unit"})
        if p.policy.exact and a.content is not None and a.content == b.content:
            reasons.append({"kind": "exact", "strength": 1, "meaning": "literal text equality"})
        if p.policy.subject and a.subject is not None and a.subject == b.subject:
            reasons.append({"kind": "subject", "strength": 1, "meaning": "declared shared subject"})
        if threshold is not None and tokens[a.id] and tokens[b.id]:
            score = Fraction(len(tokens[a.id] & tokens[b.id]), len(tokens[a.id] | tokens[b.id]))
            if score >= threshold:
                reasons.append({"kind": "near", "strength": float(score),
                                "ratio": f"{score.numerator}/{score.denominator}",
                                "meaning": "token-set Jaccard; not semantic probability"})
        if (p.policy.temporal and a.temporal_scope is not None and a.temporal_scope == b.temporal_scope
                and a.start is not None and b.start is not None):
            # Decimal spellings are exact; avoid drift and overflowing spans.
            (sa, ea), (sb, eb) = times[i], times[j]
            overlap = min(ea, eb) - max(sa, sb)
            gap = max(sa, sb) - min(ea, eb)
            if overlap > 0:
                reasons.append({"kind": "temporal", "strength": 1,
                                "overlap_ratio": str(overlap), "meaning": "half-open support overlap"})
            elif gap < embargo:
                reasons.append({"kind": "embargo", "strength": 1, "gap_ratio": str(gap),
                                "meaning": "gap strictly below embargo"})
        if reasons:
            edges.append({"a": a.id, "b": b.id, "reasons": reasons})
    return edges


def components(ids, edges):
    parent = {s: s for s in ids}
    def root(s):
        while parent[s] != s:
            parent[s] = parent[parent[s]]
            s = parent[s]
        return s
    for edge in edges:
        a, b = root(edge["a"]), root(edge["b"])
        parent[max(a, b)] = min(a, b)
    groups = {}
    for s in sorted(ids):
        groups.setdefault(root(s), []).append(s)
    return sorted(groups.values())


def explain(value, source, target):
    p = problem(value)
    ids = {s.id for s in p.samples}
    if source not in ids or target not in ids:
        raise ValueError("explanation endpoint is unknown")
    edges = relations(p)
    adjacency = {s: [] for s in ids}
    for edge in edges:
        adjacency[edge["a"]].append((edge["b"], edge))
        adjacency[edge["b"]].append((edge["a"], edge))
    queue = deque([(source, [])])
    seen = {source}
    while queue:
        node, path = queue.popleft()
        if node == target:
            return {"source": source, "target": target, "connected": True,
                    "path": path, "direct": len(path) == 1,
                    "interpretation": "isolation policy, not transitive semantic equivalence"}
        for neighbor, edge in sorted(adjacency[node], key=lambda x: x[0]):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, path + [edge]))
    return {"source": source, "target": target, "connected": False, "path": []}


def audit(value):
    p = problem(value)
    edges = relations(p)
    assignments = {s.id: s.split for s in p.samples}
    groups = components(assignments, edges)
    return {"schema": "splitleak.audit.v1", "document_digest": p.digest,
            "policy": p.policy.__dict__, "sample_count": len(p.samples), "edges": edges,
            "components": groups,
            "cross_split_edges": [e for e in edges if assignments[e["a"]] != assignments[e["b"]]],
            "conflicting_components": [g for g in groups if len({assignments[s] for s in g}) > 1],
            "scope": "declared relations only; original components remain isolated after deletions"}
