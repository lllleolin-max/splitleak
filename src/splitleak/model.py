"""Strict declared input model. Integer costs are exact arbitrary units."""
from dataclasses import dataclass
import hashlib
import json
import math


class InputError(ValueError):
    pass


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise InputError(f"{name}: expected integer >= {minimum}")
    return value


def number(value, name):
    if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
        raise InputError(f"{name}: expected finite number, excluding bool")
    return value


def string(value, name):
    if type(value) is not str or not value:
        raise InputError(f"{name}: expected nonempty string")
    return value


def keys(value, allowed, name):
    if type(value) is not dict:
        raise InputError(f"{name}: expected object")
    extra = set(value) - allowed
    if extra:
        raise InputError(f"{name}: unknown fields {sorted(extra)}")


@dataclass(frozen=True)
class Sample:
    id: str
    split: str
    content: str | None
    subject: str | None
    group: str | None
    temporal_scope: str | None
    start: int | float | None
    end: int | float | None
    allowed_splits: tuple[str, ...]
    move_cost: int
    delete_cost: int | None
    pinned: bool


@dataclass(frozen=True)
class Policy:
    exact: bool
    near_threshold: int | float | None
    subject: bool
    temporal: bool
    embargo: int | float


@dataclass(frozen=True)
class Constraints:
    min_retained: tuple[tuple[str, int], ...]
    min_total: int
    max_moves: int
    max_deletes: int
    max_cost: int | None


@dataclass(frozen=True)
class Problem:
    samples: tuple[Sample, ...]
    splits: tuple[str, ...]
    policy: Policy
    constraints: Constraints
    digest: str


def load(document: dict) -> Problem:
    keys(document, {"samples", "splits", "policy", "constraints"}, "document")
    splits = document.get("splits", ["train", "validation", "test"])
    if type(splits) is not list or not splits or len(splits) > 10:
        raise InputError("splits: expected 1..10 names")
    splits = tuple(sorted(string(s, "split") for s in splits))
    if len(set(splits)) != len(splits):
        raise InputError("splits: duplicate name")
    raw = document.get("samples")
    if type(raw) is not list or len(raw) > 200:
        raise InputError("samples: expected list of at most 200 samples")
    samples = []
    for row in raw:
        keys(row, set(Sample.__dataclass_fields__), "sample")
        ident = string(row.get("id"), "id")
        split = string(row.get("split"), "split")
        if split not in splits:
            raise InputError(f"{ident}: split is undeclared")
        content = row.get("content")
        if content is not None and (type(content) is not str or len(content) > 100_000):
            raise InputError(f"{ident}: content must be null or <=100000 characters")
        optional = []
        for name in ("subject", "group", "temporal_scope"):
            value = row.get(name)
            optional.append(None if value is None else string(value, name))
        start, end = row.get("start"), row.get("end")
        if (start is None) != (end is None):
            raise InputError(f"{ident}: supply both start/end or neither")
        if start is not None:
            number(start, "start")
            number(end, "end")
            if end <= start:
                raise InputError(f"{ident}: half-open support requires end > start")
            if optional[2] is None:
                raise InputError(f"{ident}: support requires temporal_scope")
        allowed = row.get("allowed_splits", list(splits))
        if type(allowed) is not list:
            raise InputError(f"{ident}: allowed_splits must be distinct list")
        allowed = tuple(sorted(string(s, "allowed_split") for s in allowed))
        if len(set(allowed)) != len(allowed):
            raise InputError(f"{ident}: allowed_splits must be distinct list")
        if set(allowed) - set(splits):
            raise InputError(f"{ident}: allowed_splits contains undeclared split")
        pinned = row.get("pinned", False)
        if type(pinned) is not bool:
            raise InputError(f"{ident}: pinned must be boolean")
        move_cost = integer(row.get("move_cost", 1), "move_cost")
        delete_cost = row.get("delete_cost")
        if delete_cost is not None:
            integer(delete_cost, "delete_cost")
        samples.append(Sample(ident, split, content, *optional, start, end, allowed,
                              move_cost, delete_cost, pinned))
    if len({s.id for s in samples}) != len(samples):
        raise InputError("duplicate sample IDs")
    samples.sort(key=lambda s: s.id)
    p = document.get("policy", {})
    keys(p, {"exact", "near_threshold", "subject", "temporal", "embargo"}, "policy")
    booleans = []
    for name in ("exact", "subject", "temporal"):
        value = p.get(name, True)
        if type(value) is not bool:
            raise InputError(f"policy.{name}: expected boolean")
        booleans.append(value)
    threshold = p.get("near_threshold", 0.8)
    if threshold is not None and not 0 <= number(threshold, "near_threshold") <= 1:
        raise InputError("near_threshold: expected [0,1] or null")
    embargo = number(p.get("embargo", 0), "embargo")
    if embargo < 0:
        raise InputError("embargo: expected nonnegative number")
    policy = Policy(booleans[0], threshold, booleans[1], booleans[2], embargo)
    c = document.get("constraints", {})
    keys(c, {"min_retained", "min_total", "max_moves", "max_deletes", "max_cost"}, "constraints")
    retention = c.get("min_retained", {})
    keys(retention, set(splits), "min_retained")
    retention = tuple((s, integer(retention.get(s, 0), f"min_retained.{s}")) for s in splits)
    max_cost = c.get("max_cost")
    if max_cost is not None:
        integer(max_cost, "max_cost")
    constraints = Constraints(retention, integer(c.get("min_total", 0), "min_total"),
                              integer(c.get("max_moves", len(samples)), "max_moves"),
                              integer(c.get("max_deletes", len(samples)), "max_deletes"), max_cost)
    # Canonical source commitment binds proposals to values, not filesystem paths.
    normalized = {"samples": [s.__dict__ for s in samples], "splits": splits,
                  "policy": policy.__dict__, "constraints": constraints.__dict__}
    digest = hashlib.sha256(json.dumps(normalized, sort_keys=True, ensure_ascii=False,
                                      allow_nan=False, separators=(",", ":")).encode()).hexdigest()
    return Problem(tuple(samples), splits, policy, constraints, digest)


def problem(value):
    return value if isinstance(value, Problem) else load(value)
