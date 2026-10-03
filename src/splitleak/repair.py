"""Bounded branch-and-bound over atomic repair units.

Exact exhaustive search with cost/resource pruning. Bound exhaustion is UNKNOWN;
any returned assignment is independently checked as a feasible upper bound.
"""
from .model import problem, integer
from .graph import relations, components
from .checker import check


MODES = {"full": None, "row-dedup": {"exact", "group"}, "single-group": {"subject", "group"}}


def plan(value, *, max_states=100_000, mode="full"):
    p = problem(value)
    integer(max_states, "max_states", 1)
    if mode not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    all_edges = relations(p)
    edges = all_edges if MODES[mode] is None else [e for e in all_edges
                      if any(r["kind"] in MODES[mode] for r in e["reasons"])]
    comps = components([s.id for s in p.samples], edges)
    component_of = {ident: i for i, comp in enumerate(comps) for ident in comp}
    units = {}
    for sample in p.samples:
        key = ("group", sample.group) if sample.group is not None else ("id", sample.id)
        units.setdefault(key, []).append(sample)
    units = sorted(units.values(), key=lambda u: u[0].id)
    domains = []
    for unit in units:
        choices = []
        for target in (*p.splits, None):
            if any(s.pinned and target != s.split for s in unit):
                continue
            if target is None and any(s.delete_cost is None for s in unit):
                continue
            if target is not None and any(target not in s.allowed_splits for s in unit):
                continue
            cost = sum(s.delete_cost if target is None else s.move_cost if target != s.split else 0 for s in unit)
            moves = sum(target is not None and target != s.split for s in unit)
            choices.append((cost, moves, len(unit) if target is None else 0, target))
        choices.sort(key=lambda x: (x[0], x[2], x[1], "" if x[3] is None else x[3]))
        domains.append(choices)
    c = p.constraints
    best = None
    states, exhausted = 0, False
    assigned = {}
    targets = {}
    counts = dict.fromkeys(p.splits, 0)
    def visit(depth, cost, moves, deletes):
        nonlocal states, exhausted, best
        if states >= max_states:
            exhausted = True
            return
        states += 1
        if (moves > c.max_moves or deletes > c.max_deletes or
                (c.max_cost is not None and cost > c.max_cost) or
                (best is not None and cost > best[0])):
            return
        remaining = sum(len(unit) for unit in units[depth:])
        if sum(counts.values()) + remaining < c.min_total:
            return
        if any(counts[s] + remaining < minimum for s, minimum in c.min_retained):
            return
        if depth == len(units):
            if any(counts[s] < minimum for s, minimum in c.min_retained) or sum(counts.values()) < c.min_total:
                return
            key = (cost, deletes, moves, tuple("" if assigned[s.id] is None else assigned[s.id] for s in p.samples))
            if best is None or key < best[:4]:
                best = (*key, assigned.copy())
            return
        unit = units[depth]
        comp = component_of[unit[0].id]
        for delta, moved, deleted, target in domains[depth]:
            previous = targets.get(comp)
            if target is not None and previous is not None and target != previous:
                continue
            if target is not None:
                targets[comp] = target
                counts[target] += len(unit)
            for sample in unit:
                assigned[sample.id] = target
            visit(depth + 1, cost + delta, moves + moved, deletes + deleted)
            for sample in unit:
                del assigned[sample.id]
            if target is not None:
                counts[target] -= len(unit)
                if previous is None:
                    del targets[comp]
                else:
                    targets[comp] = previous
            if exhausted:
                break
    visit(0, 0, 0, 0)
    result = {"schema": "splitleak.plan.v1", "document_digest": p.digest, "mode": mode,
              "status": "UNKNOWN" if exhausted else "OPTIMAL" if best is not None else "INFEASIBLE",
              "states_inspected": states, "max_states": max_states,
              "optimality_scope": "full policy" if mode == "full" else "baseline relation subset only",
              "assignment": None, "cost": None, "check": None}
    if best is not None:
        result.update(assignment=best[4], cost=best[0])
        result["check"] = check(p, result)
        if mode == "full" and not result["check"]["valid"]:
            raise RuntimeError("independent checker rejected optimizer candidate")
        result["bound_kind"] = "inspected feasible upper bound" if exhausted else "proven optimum within declared model"
    return result
