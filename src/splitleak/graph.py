"""Declared pairwise evidence and conservative ORIGINAL-component isolation."""
from collections import deque
from fractions import Fraction
from itertools import combinations
from .model import problem


def relations(value):
    p = problem(value)
    tokens = {s.id: set(s.content.casefold().split()) if s.content is not None else set()
              for s in p.samples}
    edges = []
    for a, b in combinations(p.samples, 2):
        reasons = []
        if a.group is not None and a.group == b.group:
            reasons.append({"kind": "group", "strength": 1, "meaning": "atomic repair unit"})
        if p.policy.exact and a.content is not None and a.content == b.content:
            reasons.append({"kind": "exact", "strength": 1, "meaning": "literal text equality"})
        if p.policy.subject and a.subject is not None and a.subject == b.subject:
            reasons.append({"kind": "subject", "strength": 1, "meaning": "declared shared subject"})
        if p.policy.near_threshold is not None and tokens[a.id] and tokens[b.id]:
            score = Fraction(len(tokens[a.id] & tokens[b.id]), len(tokens[a.id] | tokens[b.id]))
            if score >= Fraction(str(p.policy.near_threshold)):
                reasons.append({"kind": "near", "strength": float(score),
                                "ratio": f"{score.numerator}/{score.denominator}",
                                "meaning": "token-set Jaccard; not semantic probability"})
        if (p.policy.temporal and a.temporal_scope is not None and a.temporal_scope == b.temporal_scope
                and a.start is not None and b.start is not None):
            overlap = min(a.end, b.end) - max(a.start, b.start)
            gap = max(a.start, b.start) - min(a.end, b.end)
            if overlap > 0:
                reasons.append({"kind": "temporal", "strength": 1,
                                "overlap": overlap, "meaning": "half-open support overlap"})
            elif gap < p.policy.embargo:
                reasons.append({"kind": "embargo", "strength": 1, "gap": gap,
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
