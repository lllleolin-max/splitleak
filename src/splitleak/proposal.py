"""Apply to a NEW assignment manifest, never mutate the source dataset."""
from .model import problem, InputError
from .checker import check


def apply(value, proposal):
    p = problem(value)
    verdict = check(p, proposal)
    if not verdict["valid"]:
        raise InputError("proposal rejected: " + "; ".join(verdict["errors"]))
    return {"schema": "splitleak.assignment.v1", "document_digest": p.digest,
            "assignment": dict(sorted(proposal["assignment"].items())), "cost": verdict["cost"],
            "check": verdict, "scope": "join IDs to source locally; null means exclude entire repair group"}
