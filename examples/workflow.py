"""Real installed SDK workflow with JSON artifacts; sources are never changed."""
import argparse
import json
from pathlib import Path
from splitleak import load, audit, explain, plan, apply, check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/sdk")
    args = parser.parse_args()
    root = Path(__file__).parent
    d = json.loads((root / "transitive.json").read_text())
    p = load(d)
    proposed = plan(p)
    manifest = apply(p, proposed)
    inspected = check(p, manifest)
    assert inspected["valid"] and proposed["status"] == "OPTIMAL"
    results = {"audit": audit(p), "path": explain(p, "A", "D"), "plan": proposed,
               "manifest": manifest, "check": inspected}
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    for name, result in results.items():
        (output / f"{name}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": proposed["status"], "cost": proposed["cost"],
                      "retained": inspected["retained"], "residual_edges": len(inspected["residual_cross_split_edges"]),
                      "path_hops": len(results["path"]["path"])}))


if __name__ == "__main__":
    main()
