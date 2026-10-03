"""Independent feasibility checker: no optimizer or graph-builder imports.

Recomputes pair evidence and reachability from the validated source, not a
proposal's edges. This is independent implementation, not independent authorship.
"""
from .model import problem


def supported(a, b, policy):
    if a.group is not None and a.group == b.group:
        return True
    if policy.exact and a.content is not None and a.content == b.content:
        return True
    if policy.subject and a.subject is not None and a.subject == b.subject:
        return True
    if policy.near_threshold is not None and a.content is not None and b.content is not None:
        left, right = set(a.content.casefold().split()), set(b.content.casefold().split())
        if left and right:
            # Rational comparison is independent of graph's Fraction scoring.
            from decimal import Decimal
            threshold = Decimal(str(policy.near_threshold))
            if Decimal(len(left & right)) >= threshold * len(left | right):
                return True
    if (policy.temporal and a.temporal_scope is not None and a.temporal_scope == b.temporal_scope
            and a.start is not None and b.start is not None):
        if a.start < b.end and b.start < a.end:
            return True
        distance = b.start - a.end if a.end <= b.start else a.start - b.end
        if distance < policy.embargo:
            return True
    return False


def check(value, proposal):
    p = problem(value)
    errors = []
    if type(proposal) is not dict:
        return {"valid": False, "errors": ["proposal must be object"]}
    if proposal.get("document_digest") != p.digest:
        errors.append("source commitment mismatch")
    assignment = proposal.get("assignment")
    ids = {s.id for s in p.samples}
    if type(assignment) is not dict or set(assignment) != ids:
        return {"valid": False, "errors": errors + ["assignment must contain every source ID exactly once"]}
    counts = {s: 0 for s in p.splits}
    cost = moves = deletes = 0
    hard_groups = {}
    for s in p.samples:
        target = assignment[s.id]
        if target is not None and (type(target) is not str or target not in p.splits):
            return {"valid": False, "errors": errors + [f"{s.id}: invalid target"]}
        if s.pinned and target != s.split:
            errors.append(f"{s.id}: pin violated")
        if target is None:
            deletes += 1
            if s.delete_cost is None:
                errors.append(f"{s.id}: deletion forbidden")
            else:
                cost += s.delete_cost
        else:
            counts[target] += 1
            if target not in s.allowed_splits:
                errors.append(f"{s.id}: destination forbidden")
            if target != s.split:
                moves += 1
                cost += s.move_cost
        if s.group is not None:
            hard_groups.setdefault(s.group, set()).add(target)
    if any(len(destinations) > 1 for destinations in hard_groups.values()):
        errors.append("atomic group split or partially deleted")
    adjacency = {s.id: set() for s in p.samples}
    residual = []
    for i, a in enumerate(p.samples):
        for b in p.samples[i+1:]:
            if supported(a, b, p.policy):
                adjacency[a.id].add(b.id)
                adjacency[b.id].add(a.id)
                if assignment[a.id] is not None and assignment[b.id] is not None and assignment[a.id] != assignment[b.id]:
                    residual.append([a.id, b.id])
    seen = set()
    component_conflicts = []
    for ident in sorted(ids):
        if ident in seen:
            continue
        pending, members = [ident], set()
        while pending:
            current = pending.pop()
            if current in members:
                continue
            members.add(current)
            pending.extend(adjacency[current] - members)
        seen.update(members)
        retained = {assignment[s] for s in members} - {None}
        if len(retained) > 1:
            component_conflicts.append(sorted(members))
    if component_conflicts:
        errors.append("original-component isolation violated")
    c = p.constraints
    if sum(counts.values()) < c.min_total:
        errors.append("minimum total retention violated")
    for split, minimum in c.min_retained:
        if counts[split] < minimum:
            errors.append(f"minimum retention violated: {split}")
    if moves > c.max_moves:
        errors.append("move limit exceeded")
    if deletes > c.max_deletes:
        errors.append("delete limit exceeded")
    if c.max_cost is not None and cost > c.max_cost:
        errors.append("cost cap exceeded")
    if "cost" in proposal and (type(proposal["cost"]) is not int or proposal["cost"] != cost):
        errors.append("claimed cost mismatch")
    return {"valid": not errors, "errors": errors, "cost": cost, "moves": moves,
            "deletes": deletes, "retained": counts, "retained_total": sum(counts.values()),
            "residual_cross_split_edges": residual, "component_conflicts": component_conflicts,
            "certification": "feasibility only, declared relations and original-component isolation"}
