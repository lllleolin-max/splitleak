from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sysconfig
from tempfile import TemporaryDirectory
import unittest
from splitleak.cli import main, read, MAX_JSON_BYTES
from splitleak import InputError, audit


class CLITests(unittest.TestCase):
    def test_unicode_console_json_and_unchanged_utf8_output(self):
        console = Path(sysconfig.get_path('scripts')) / ('splitleak.exe' if os.name == 'nt' else 'splitleak')
        document = {'samples': [{'id': 'A\U0001f642', 'split': 'train', 'content': '\u4e2d\u6587 Stra\u00dfe'}]}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.json'
            saved = json.dumps(audit(document), ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + '\n'
            for encoding in ('cp936', 'cp1252', 'utf-8'):
                env = dict(os.environ, PYTHONIOENCODING=encoding)
                source.write_text(json.dumps(document, ensure_ascii=False), encoding='utf-8')
                original = source.read_bytes()
                result = subprocess.run([str(console), 'audit', str(source)], capture_output=True, env=env)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, b'')
                self.assertTrue(result.stdout.isascii())
                self.assertEqual(json.loads(result.stdout), audit(document))
                output = root / (encoding + '.json')
                result = subprocess.run([str(console), 'audit', str(source), '--out', str(output)], capture_output=True, env=env)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b'', b''))
                self.assertEqual(output.read_bytes(), saved.encode('utf-8'))
                self.assertEqual(source.read_bytes(), original)
                invalid = dict(document, samples=[dict(document['samples'][0], start=1)])
                source.write_text(json.dumps(invalid, ensure_ascii=False), encoding='utf-8')
                original = source.read_bytes()
                refused = root / (encoding + '-invalid.json')
                result = subprocess.run([str(console), 'audit', str(source), '--out', str(refused)], capture_output=True, env=env)
                self.assertEqual((result.returncode, result.stdout), (2, b''))
                self.assertTrue(result.stderr.isascii())
                self.assertIn('A\U0001f642', json.loads(result.stderr)['error'])
                self.assertFalse(refused.exists())
                self.assertEqual(source.read_bytes(), original)

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

    def test_depth_scanner_ignores_brackets_and_escaped_quotes_in_strings(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            value = {"samples": [], "note": '[' * 2000 + '\\"' + ']' * 2000}
            source.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(read(source), value)

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
