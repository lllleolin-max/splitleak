"""Run the real release harness with an isolated prefix-root interpreter.

This reproduces separation of Python and console scripts, as in a normal
Windows installation, without installing anything into the user's Python.
The copied venv interpreter is a layout regression, not a global-install test.
It requires Windows Python 3.14+, whose path initialization preserves the
isolated prefix when pyvenv.cfg is next to the copied interpreter.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import venv


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", required=True)
    parser.add_argument("--harness", default=str(root / "tools/verify_release.py"))
    args = parser.parse_args()
    if os.name != "nt" or sys.version_info < (3, 14):
        parser.error("this layout probe requires Windows Python 3.14+")
    wheel, harness = Path(args.wheel).resolve(), Path(args.harness).resolve()
    output = root / ".local" / ("console-layout-" + uuid.uuid4().hex[:10])
    env = output / "env"
    venv.EnvBuilder(with_pip=True, symlinks=False).create(env)
    env_python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    def execute(command, name):
        result = subprocess.run([str(part) for part in command], capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        (output / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        assert result.returncode == 0, f"{name} failed; inspect ignored local logs"
        return result.stdout

    execute([env_python, "-m", "pip", "install", "--no-deps", wheel], "install")
    prefix_python = env / env_python.name
    shutil.copy2(env_python, prefix_python)
    metadata = json.loads(execute([prefix_python, "-c",
        "import json,sys,sysconfig,pathlib,splitleak; "
        "print(json.dumps({'isolated':sys.prefix!=sys.base_prefix,"
        "'prefix_root':pathlib.Path(sys.executable).parent==pathlib.Path(sys.prefix),"
        "'scripts':sysconfig.get_path('scripts'),"
        "'wheel_import':'site-packages' in splitleak.__file__}))"], "layout"))
    assert metadata["isolated"] and metadata["prefix_root"] and metadata["wheel_import"]
    console_name = "splitleak.exe" if os.name == "nt" else "splitleak"
    console = Path(metadata["scripts"]) / console_name
    assert console.is_file() and not (prefix_python.parent / console_name).exists()
    verified = json.loads(execute([prefix_python, harness], "harness"))
    assert verified["console_steps"] == 5 and verified["exit_codes"] == [0] * 5
    print(json.dumps({"layout": "isolated prefix-root interpreter / separate scripts",
                      "wheel_import": "site-packages", "adjacent_console_exists": False,
                      "console_steps": verified["console_steps"],
                      "exit_codes": verified["exit_codes"],
                      "source_unchanged": verified["source_unchanged"]}))


if __name__ == "__main__":
    main()
