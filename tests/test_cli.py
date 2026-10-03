from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from splitleak.cli import main, read, MAX_JSON_BYTES
from splitleak import InputError


class CLITests(unittest.TestCase):
    def test_reject_ambiguous_json_policy_and_assignment(self):
        ambiguous = [
            '{"samples":[],"policy":{"subject":false,"subject":true}}',
            '{"assignment":{"A":"test","A":"train"}}',
            '{"samples":[{"id":"A","id":"B","split":"train"}]}',
            '{"samples":[],"policy":{"embargo":NaN}}',
            '[' * 2000 + '0' + ']' * 2000,
        ]
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            for payload in ambiguous:
                source.write_text(payload, encoding="utf-8")
                with self.subTest(payload=payload[:60]), self.assertRaises(InputError):
                    read(source)
                with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                    self.assertEqual(main(["audit", str(source)]), 2)

    def test_json_byte_limit(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "large.json"
            with source.open("wb") as stream:
                stream.write(b" " * (MAX_JSON_BYTES + 1))
            with self.assertRaisesRegex(InputError, "32 MiB"):
                read(source)

    def test_cli_complete_workflow_and_refused_overwrite(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, proposal, manifest = [root / name for name in ("source.json", "proposal.json", "manifest.json")]
            data = {"samples": [{"id": "A", "split": "train", "content": "same"},
                                {"id": "B", "split": "test", "content": "same"}]}
            source.write_text(json.dumps(data), encoding="utf-8")
            original = source.read_bytes()
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(main(["plan", str(source), "--out", str(proposal)]), 0)
                self.assertEqual(main(["apply", str(source), str(proposal), "--out", str(manifest)]), 0)
                self.assertEqual(main(["check", str(source), str(manifest)]), 0)
                self.assertEqual(main(["audit", str(source), "--out", str(source)]), 2)
                self.assertEqual(main(["plan", str(source), "--max-states", "1"]), 4)
            self.assertEqual(source.read_bytes(), original)
            self.assertTrue(json.loads(manifest.read_text())["check"]["valid"])


if __name__ == "__main__":
    unittest.main()
