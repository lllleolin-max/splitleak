"""Regression: duplicate JSON keys must not silently choose a policy."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from splitleak.cli import main


def run():
    ambiguous = '{"splits":["train","test"],"samples":[],"policy":{"subject":false,"subject":true}}'
    with TemporaryDirectory() as tmp:
        source = Path(tmp) / "ambiguous.json"
        source.write_text(ambiguous, encoding="utf-8")
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()) as error:
            code = main(["audit", str(source)])
        assert code == 2 and "duplicate JSON key" in error.getvalue(), "ambiguous JSON policy accepted"
    print("review_3: PASS (duplicate JSON policy key rejected, exit 2)")


if __name__ == "__main__":
    run()
