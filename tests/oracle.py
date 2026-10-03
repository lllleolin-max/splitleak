"""Independent small exhaustive oracle: row Cartesian product + Floyd closure.

No imports from SplitLeak. Meant for <=8 synthetic rows, not production use.
"""
from fractions import Fraction
from itertools import product


def optimum(document):
    rows = sorted(document["samples"], key=lambda r: r["id"])
    splits = sorted(document.get("splits", ["train", "validation", "test"]))
    if len(rows) > 8:
        raise ValueError("oracle supports <=8 rows")
    policy = document.get("policy", {})
    n = len(rows)
    reach = [[i == j for j in range(n)] for i in range(n)]
    for i, a in enumerate(rows):
        for j, b in enumerate(rows):
            linked = (a.get("group") is not None and a.get("group") == b.get("group"))
            linked |= (policy.get("exact", True) and a.get("content") is not None and a.get("content") == b.get("content"))
            linked |= (policy.get("subject", True) and a.get("subject") is not None and a.get("subject") == b.get("subject"))
            threshold = policy.get("near_threshold", 0.8)
            left, right = set((a.get("content") or "").casefold().split()), set((b.get("content") or "").casefold().split())
            if threshold is not None and left and right:
                linked |= Fraction(len(left & right), len(left | right)) >= Fraction(str(threshold))
            if (policy.get("temporal", True) and a.get("temporal_scope") is not None and a.get("temporal_scope") == b.get("temporal_scope")
                    and a.get("start") is not None and b.get("start") is not None):
                sa, ea, sb, eb = (Fraction(str(x)) for x in (a["start"], a["end"], b["start"], b["end"]))
                overlap = max(sa, sb) < min(ea, eb)
                gap = max(sa, sb) - min(ea, eb)
                linked |= overlap or gap < Fraction(str(policy.get("embargo", 0)))
            reach[i][j] = bool(reach[i][j] or linked)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                reach[i][j] |= reach[i][k] and reach[k][j]
    c = document.get("constraints", {})
    best = None
    for destinations in product([*splits, None], repeat=n):
        groups, counts = {}, dict.fromkeys(splits, 0)
        cost = moves = deletes = 0
        valid = True
        for row, dest in zip(rows, destinations):
            if row.get("pinned", False) and dest != row["split"]:
                valid = False
            if dest is None:
                deletes += 1
                if row.get("delete_cost") is None:
                    valid = False
                else:
                    cost += row["delete_cost"]
            else:
                counts[dest] += 1
                if dest not in row.get("allowed_splits", splits):
                    valid = False
                if dest != row["split"]:
                    moves += 1
                    cost += row.get("move_cost", 1)
            if row.get("group") is not None:
                groups.setdefault(row["group"], set()).add(dest)
        valid &= all(len(targets) == 1 for targets in groups.values())
        valid &= all(not reach[i][j] or a is None or b is None or a == b
                     for i, a in enumerate(destinations) for j, b in enumerate(destinations))
        valid &= moves <= c.get("max_moves", n) and deletes <= c.get("max_deletes", n)
        valid &= c.get("max_cost") is None or cost <= c["max_cost"]
        valid &= sum(counts.values()) >= c.get("min_total", 0)
        valid &= all(counts[s] >= minimum for s, minimum in c.get("min_retained", {}).items())
        if valid:
            key = (cost, deletes, moves, tuple("" if s is None else s for s in destinations))
            if best is None or key < best[0]:
                best = (key, dict(zip([r["id"] for r in rows], destinations)))
    return best
