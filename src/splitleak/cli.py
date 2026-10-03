import argparse
import json
from pathlib import Path
import sys
from . import InputError, load, audit, explain, plan, check, apply


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Declared split-contamination audit and repair")
    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("audit", "plan", "check", "apply", "explain"):
        sub = subs.add_parser(name)
        sub.add_argument("input", help="source problem JSON")
        sub.add_argument("--out", help="new JSON output file; existing files refused")
        if name in ("check", "apply"):
            sub.add_argument("proposal")
        if name == "plan":
            sub.add_argument("--max-states", type=int, default=100_000)
        if name == "explain":
            sub.add_argument("source")
            sub.add_argument("target")
    args = parser.parse_args(argv)
    try:
        p = load(read(args.input))
        code = 0
        if args.command == "audit":
            result = audit(p)
        elif args.command == "explain":
            result = explain(p, args.source, args.target)
        elif args.command == "plan":
            result = plan(p, max_states=args.max_states)
            code = {"OPTIMAL": 0, "INFEASIBLE": 3, "UNKNOWN": 4}[result["status"]]
        elif args.command == "check":
            result = check(p, read(args.proposal))
            code = 0 if result["valid"] else 5
        else:
            result = apply(p, read(args.proposal))
        payload = json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n"
        if args.out:
            with Path(args.out).open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
        else:
            print(payload, end="")
        return code
    except (InputError, ValueError, OSError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
