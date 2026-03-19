"""Tests for batch_decode_dataflows module."""

import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from batch_decode_dataflows import decode_dataflow_definition, batch_decode_directory  # noqa: E402


class TestDecodeDataflowDefinition(unittest.TestCase):
    def _make_export(self, parts):
        return {"definition": {"parts": parts}}

    def _encode_part(self, path, content, is_json=False):
        if is_json:
            payload = base64.b64encode(json.dumps(content).encode('utf-8')).decode('ascii')
        else:
            payload = base64.b64encode(content.encode('utf-8')).decode('ascii')
        return {"path": path, "payload": payload, "payloadType": "InlineBase64"}

    def test_decode_basic_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export = self._make_export([
                self._encode_part("mashup.pq", "let Source = 1 in Source"),
                self._encode_part("queryMetadata.json", {"queriesMetadata": {}}, is_json=True),
            ])
            input_file = Path(tmpdir) / "export.json"
            input_file.write_text(json.dumps(export), encoding='utf-8')
            output_dir = Path(tmpdir) / "output"

            result = decode_dataflow_definition(input_file, output_dir)

            self.assertTrue(result)
            self.assertTrue((output_dir / "mashup.pq").exists())
            self.assertTrue((output_dir / "queryMetadata.json").exists())
            self.assertTrue((output_dir / "definition_decoded.json").exists())
            self.assertEqual(
                (output_dir / "mashup.pq").read_text(encoding='utf-8'),
                "let Source = 1 in Source"
            )

    def test_decode_none_path_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export = self._make_export([
                {"path": None, "payload": "dGVzdA==", "payloadType": "InlineBase64"},
                self._encode_part("mashup.pq", "let X = 1 in X"),
            ])
            input_file = Path(tmpdir) / "export.json"
            input_file.write_text(json.dumps(export), encoding='utf-8')
            output_dir = Path(tmpdir) / "output"

            result = decode_dataflow_definition(input_file, output_dir)
            self.assertTrue(result)
            self.assertTrue((output_dir / "mashup.pq").exists())

    def test_decode_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export = self._make_export([
                self._encode_part("../../evil.txt", "malicious content"),
            ])
            input_file = Path(tmpdir) / "export.json"
            input_file.write_text(json.dumps(export), encoding='utf-8')
            output_dir = Path(tmpdir) / "output"

            result = decode_dataflow_definition(input_file, output_dir)
            self.assertTrue(result)
            # Path traversal stripped to basename — file inside output_dir
            self.assertFalse((Path(tmpdir) / "evil.txt").exists())
            self.assertTrue((output_dir / "evil.txt").exists())

    def test_backup_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export = self._make_export([
                self._encode_part("mashup.pq", "test"),
            ])
            input_file = Path(tmpdir) / "test_export.json"
            input_file.write_text(json.dumps(export), encoding='utf-8')
            output_dir = Path(tmpdir) / "output"

            decode_dataflow_definition(input_file, output_dir)
            self.assertTrue((output_dir / "test_export.json").exists())


class TestBatchDecodeDirectory(unittest.TestCase):
    def test_batch_decode_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                export = {"definition": {"parts": [
                    {"path": "mashup.pq",
                     "payload": base64.b64encode(f"query {i}".encode()).decode(),
                     "payloadType": "InlineBase64"}
                ]}}
                (Path(tmpdir) / f"WS__ws{i}__id{i}__Name{i}__Dataflow.json").write_text(
                    json.dumps(export), encoding='utf-8')

            result = batch_decode_directory(tmpdir)
            self.assertTrue(result)

            mapping = Path(tmpdir) / "item_mapping.txt"
            self.assertTrue(mapping.exists())
            lines = mapping.read_text(encoding='utf-8').strip().split('\n')
            self.assertEqual(len(lines), 3)

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = batch_decode_directory(tmpdir)
            self.assertFalse(result)

    def test_nonexistent_directory(self):
        result = batch_decode_directory("/nonexistent/path/xyz_does_not_exist")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
