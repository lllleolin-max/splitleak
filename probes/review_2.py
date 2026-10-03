"""Regression: decimal embargo equality and finite extreme spans."""
import json
from splitleak import audit, check, load


def run():
    equality = {"splits": ["train", "test"], "policy": {"near_threshold": None, "embargo": 0.2},
                "samples": [{"id": "A", "split": "train", "temporal_scope": "s", "start": 0, "end": 0.1},
                            {"id": "B", "split": "test", "temporal_scope": "s", "start": 0.3, "end": 0.4}]}
    assert not audit(equality)["edges"], "decimal gap == embargo incorrectly linked"
    assert check(equality, {"document_digest": load(equality).digest,
                            "assignment": {"A": "train", "B": "test"}})["valid"]
    extreme = {"samples": [{"id": "A", "split": "train", "temporal_scope": "s", "start": -1e308, "end": 1e308},
                           {"id": "B", "split": "test", "temporal_scope": "s", "start": -1e308, "end": 1e308}]}
    json.dumps(audit(extreme), allow_nan=False)
    print("review_2: PASS (decimal equality allowed; extreme finite evidence serializes)")


if __name__ == "__main__":
    run()
