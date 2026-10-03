"""Build archive wheels; run SAME probes against before/after installed code.

Requires git and `python -m pip install build`. Raw logs/archives remain in
ignored .local; public JSON contains SHA/exit/finding only. No source mutation.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import venv
import zipfile


def main():
    root = Path(__file__).resolve().parents[1]
    index = json.loads((root / "docs/ITERATION_INDEX.json").read_text())
    local = root / ".local" / ("archive-replay-" + uuid.uuid4().hex[:10])
    local.mkdir(parents=True)
    interpreters = {}
    def execute(command, cwd, log):
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        return result
    for sha in dict.fromkeys(r[state] for r in index for state in ["before", "after"]):
        print(json.dumps({"phase": "build_archive_wheel", "sha": sha}), flush=True)
        checkout = local / sha
        checkout.mkdir()
        archive = local / f"{sha}.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--output={archive}", sha], cwd=root, check=True)
        with zipfile.ZipFile(archive) as package:
            package.extractall(checkout)
        built = execute([sys.executable, "-m", "build", "--wheel"], checkout, local / f"{sha}-build.log")
        if built.returncode:
            raise RuntimeError(f"archive wheel build failed at {sha}; inspect ignored local logs")
        target = local / f"{sha}-venv"
        venv.EnvBuilder(with_pip=True).create(target)
        python = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        wheel = next((checkout / "dist").glob("*.whl"))
        installed = execute([str(python), "-m", "pip", "install", str(wheel)], checkout, local / f"{sha}-install.log")
        if installed.returncode:
            raise RuntimeError(f"archive wheel install failed at {sha}")
        imported = execute([str(python), "-c", "import splitleak; assert 'site-packages' in splitleak.__file__"],
                           checkout, local / f"{sha}-import.log")
        assert imported.returncode == 0, "archive import not from wheel"
        interpreters[sha] = (python, checkout)
    records = []
    for row in index:
        for state, expected in [("before", 1), ("after", 0)]:
            sha = row[state]
            python, checkout = interpreters[sha]
            probe = execute([str(python), str(root / row["probe"])], checkout,
                            local / f"cycle-{row['cycle']}-{state}.log")
            assert probe.returncode == expected, f"unexpected probe exit at cycle {row['cycle']} {state}"
            if state == "before":
                assert row["failure"] in probe.stderr, "before failed for unrelated reason"
            record = {"cycle": row["cycle"], "state": state, "sha": sha,
                      "wheel_import": "site-packages", "probe_exit": probe.returncode,
                      "finding": row["failure"] if state == "before" else probe.stdout.strip()}
            if state == "after":
                tests = execute([str(python), "-m", "unittest", "discover", "-s", "tests", "-v"], checkout,
                                local / f"cycle-{row['cycle']}-tests.log")
                assert tests.returncode == 0, f"archived after tests failed at cycle {row['cycle']}"
                assert f"Ran {row['after_tests']} tests" in tests.stderr, "unexpected archive test count"
                record["tests"] = row["after_tests"]
                record["test_exit"] = tests.returncode
            records.append(record)
            print(json.dumps(record), flush=True)
    (local / "REPLAY_SUMMARY.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print("archive replay: PASS (three actual before-fail/after-pass cycles; raw logs ignored)")


if __name__ == "__main__":
    main()
