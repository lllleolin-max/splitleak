"""Executed structural ablations, not benchmarks of incumbent software.

Every mode uses SAME source policy, pins, permissions, costs and retention.
Baselines optimize only their named relation subset, then full checker scores
residual contamination. This makes unsupported claims falsifiable.
"""
import argparse
import copy
import json
from pathlib import Path
from splitleak import plan


def run():
    rows = []
    root = Path(__file__).parents[1] / "examples"
    for fixture in ["transitive", "baseline_succeeds", "conservative_chain"]:
        d = json.loads((root / f"{fixture}.json").read_text())
        for mode in ["row-dedup", "single-group", "full"]:
            p = plan(d, mode=mode)
            checked = p["check"]
            rows.append({"case": fixture, "mode": mode, "status": p["status"], "cost": p["cost"],
                         "retained": None if checked is None else checked["retained_total"],
                         "residual_edges": None if checked is None else len(checked["residual_cross_split_edges"]),
                         "component_conflicts": None if checked is None else len(checked["component_conflicts"]),
                         "full_policy_valid": False if checked is None else checked["valid"],
                         "states": p["states_inspected"]})
    chain = json.loads((root / "conservative_chain.json").read_text())
    sensitivity = []
    for threshold in [None, 0, 0.34, 0.66, 0.9, 1]:
        d = copy.deepcopy(chain)
        d["policy"]["near_threshold"] = threshold
        p = plan(d)
        sensitivity.append({"threshold": threshold, "status": p["status"], "cost": p["cost"]})
    assert next(r for r in rows if r["case"] == "transitive" and r["mode"] == "full")["full_policy_valid"]
    assert all(r["full_policy_valid"] for r in rows if r["case"] == "baseline_succeeds")
    assert next(r for r in rows if r["case"] == "conservative_chain" and r["mode"] == "full")["status"] == "INFEASIBLE"
    return {"fixture_kind": "disclosed synthetic", "same_constraints_across_modes": True,
            "comparison": rows, "threshold_sensitivity": sensitivity,
            "claims": "policy contamination and retention only; no observed ML or customer gain"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out")
    args = parser.parse_args()
    payload = json.dumps(run(), sort_keys=True, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    print(payload, end="")
