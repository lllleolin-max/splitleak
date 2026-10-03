"""Executed installed-wheel and REAL console workflow smoke verification."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sysconfig
import uuid
import splitleak


def main():
    assert "site-packages" in splitleak.__file__, "use a normal installed wheel"
    root = Path(__file__).resolve().parents[1]
    source = root / "examples/transitive.json"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    output = root / ".local" / ("release-" + uuid.uuid4().hex[:10])
    output.mkdir(parents=True)
    # A global Windows interpreter has its console scripts under Scripts.
    console = Path(sysconfig.get_path("scripts")) / ("splitleak.exe" if os.name == "nt" else "splitleak")
    commands = [
        ["audit", str(source), "--out", str(output / "audit.json")],
        ["explain", str(source), "A", "D", "--out", str(output / "path.json")],
        ["plan", str(source), "--out", str(output / "proposal.json")],
        ["apply", str(source), str(output / "proposal.json"), "--out", str(output / "manifest.json")],
        ["check", str(source), str(output / "manifest.json"), "--out", str(output / "check.json")],
    ]
    for command in commands:
        result = subprocess.run([str(console), *command], capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        (output / f"{command[0]}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        assert result.returncode == 0, f"console {command[0]} failed; inspect ignored local logs"
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    verdict = json.loads((output / "check.json").read_text())
    proposed = json.loads((output / "proposal.json").read_text())
    path = json.loads((output / "path.json").read_text())
    assert before == after and verdict["valid"] and proposed["status"] == "OPTIMAL"
    assert proposed["cost"] == 2 and verdict["retained_total"] == 6
    print(json.dumps({"wheel_import": "site-packages", "console_steps": 5, "exit_codes": [0] * 5,
                      "source_unchanged": True, "cost": proposed["cost"], "retained": verdict["retained"],
                      "residual_edges": len(verdict["residual_cross_split_edges"]), "path_hops": len(path["path"])}))


if __name__ == "__main__":
    main()
