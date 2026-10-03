# Console verification portability correction

Executed locally on 2026-10-03: Windows, CPython 3.14.3. This is a verification-tool correction after predecessor `5f2fe8fe488103ef614b6423983555c1ae43b71f`, not another algorithm review cycle. The three historical cycles, intermediate failed `bb72c44` result and earlier verification record remain unchanged. Existing independent scores belong to their reviewed predecessor; this patch requires a separate review and actual remote CI before publication approval.

The root's recorded remote Actions run [37089523094](https://github.com/lllleolin-max/splitleak/actions/runs/37089523094) exposed a Windows harness failure after normal wheel installation, tests, SDK and contrast passed. `tools/verify_release.py` assumed that the console executable was next to `sys.executable`. A global Windows Python installation places Python at its prefix root and pip's console scripts under `Scripts`; a normal Windows venv places both under `Scripts`, hiding that assumption in earlier local verification.

The harness now obtains the running interpreter's scripts directory from `sysconfig.get_path("scripts")`, retaining the Windows `.exe` suffix and POSIX console name. It executes the installed console directly for audit, explain, plan, apply and check; it does not search PATH or replace those calls with Python module calls. All original result and source-preservation assertions remain. Package source, SDK, algorithm, tests, fixtures, benchmark results and version 0.1.0 are unchanged.

## Live layout reproduction

[probes/console_layout.py](../probes/console_layout.py) creates a fresh isolated venv, installs the ordinary wheel, then copies that venv's Python executable to its prefix root while retaining the actual pip console in `Scripts`. It asserts an isolated prefix, a site-packages import, an existing scripts console and no adjacent console before executing the named release harness. The pre-fix harness was exported from the exact predecessor with `git archive` and run against the same unchanged wheel core to isolate the harness defect.

This focused probe requires Windows Python 3.14+ and is included in the Windows 3.14 CI job. Python 3.14 initializes the venv prefix before `site`; the copied interpreter emits site-prefix RuntimeWarnings, retained in ignored raw logs, while the probe asserts the actual prefix and import remain isolated. This is an executable-layout reproduction, **not** a claim that a local global installation or Python 3.11/Linux was tested. The ordinary release harness still runs in every Ubuntu/Windows × Python 3.11/3.14 CI job. Results for the new remote run are pending root verification.

Actual local commands, with `python` denoting the fresh normal-wheel environment `.venv-console-fixed-final` unless marked builder:

| Command | Observed result |
|---|---|
| Builder `python -m build --wheel`; fresh venv `python -m pip install dist/splitleak-0.1.0-py3-none-any.whl` | Build and normal install exit 0; site-packages import asserted |
| `git archive --format=zip --output=.local/console-portability/before.zip 5f2fe8fe488103ef614b6423983555c1ae43b71f` followed by ZIP extraction | Exact old harness and fixture exported; no source checkout edits |
| `python probes/console_layout.py --wheel dist/splitleak-0.1.0-py3-none-any.whl --harness .local/console-portability/before/tools/verify_release.py` | Exit 1; actual harness log contains `FileNotFoundError: [WinError 2]` at console launch |
| `python probes/console_layout.py --wheel dist/splitleak-0.1.0-py3-none-any.whl` | Exit 0; five real console exits 0, source unchanged, no adjacent console |
| `python tools/verify_release.py` | Ordinary venv: five real console exits 0, source unchanged, cost 2, retained train=5/test=1, residual edges 0, path hops 3 |
| `python -m unittest discover -s tests -v` | 19 tests, OK, 0.341 seconds |
| `python examples/workflow.py --output .local/console-portability/final-sdk` | OPTIMAL, cost 2, retained train=5/test=1, residual edges 0, path hops 3 |
| `python benchmarks/contrast.py --out .local/console-portability/final-contrast.json` | Nine comparisons and six threshold settings; parsed output exactly matches tracked `benchmarks/RESULTS.json` |
| `python ../reviews/independent_second_sol_splitleak_probe.py` | Frozen peer probe SHA256 `8764ca85d3ae3b2df074f88199d5322aca4755dfa7c8183a2173407edea0cfc6`; 96 cases, 19 OPTIMAL/77 INFEASIBLE, all adversarial checks pass |

The peer probe lives in the external portfolio review workspace and is not part of this package. It was run read-only; this builder rerun does not replace separate independent review at the new commit. Redacted observed outputs are in [CONSOLE_PORTABILITY_RESULTS.json](CONSOLE_PORTABILITY_RESULTS.json). Raw paths, tracebacks and console artifacts remain ignored under `.local/`. No global installation, publication, tag or release was performed by this correction task.
