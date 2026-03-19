"""Tests for create_pqt_from_workspace module."""

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from create_pqt_from_workspace import (  # noqa: E402
    create_mashup_metadata,
    create_metadata,
    create_pqt_archive,
    create_pqtzip_structure,
    find_dataflow_items,
    read_item_mapping,
    copy_dataflow_items,
)
from shared_utils import PQT_VERSION  # noqa: E402


class TestCreateMashupMetadata(unittest.TestCase):
    def test_basic_transformation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata = {
                "queriesMetadata": {
                    "Query1": {"isHidden": False},
                    "Query2": {"isHidden": True}
                }
            }
            path = Path(tmpdir) / "queryMetadata.json"
            path.write_text(json.dumps(metadata), encoding='utf-8')

            result = create_mashup_metadata(path)
            self.assertEqual(result['Version'], PQT_VERSION)
            self.assertEqual(len(result['QueriesMetadata']), 2)
            names = [q['Name'] for q in result['QueriesMetadata']]
            self.assertIn('Query1', names)
            self.assertIn('Query2', names)

    def test_empty_queries_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "queryMetadata.json"
            path.write_text(json.dumps({"queriesMetadata": {}}), encoding='utf-8')

            result = create_mashup_metadata(path)
            self.assertEqual(result['QueriesMetadata'], [])

    def test_missing_queries_metadata_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "queryMetadata.json"
            path.write_text(json.dumps({"otherKey": "value"}), encoding='utf-8')

            result = create_mashup_metadata(path)
            self.assertEqual(result['QueriesMetadata'], [])


class TestCreateMetadata(unittest.TestCase):
    def test_extracts_display_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            platform = {"config": {"displayName": "My Dataflow"}}
            path = Path(tmpdir) / ".platform"
            path.write_text(json.dumps(platform), encoding='utf-8')

            result = create_metadata(path)
            self.assertEqual(result['Name'], 'My Dataflow')
            self.assertEqual(result['Version'], PQT_VERSION)
            self.assertEqual(result['Description'], '')

    def test_missing_display_name_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / ".platform"
            path.write_text(json.dumps({"config": {}}), encoding='utf-8')

            result = create_metadata(path)
            self.assertEqual(result['Name'], 'Dataflow')


class TestFindDataflowItems(unittest.TestCase):
    def test_finds_items_with_mashup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            item1 = Path(tmpdir) / "item_001"
            item1.mkdir()
            (item1 / "mashup.pq").write_text("query", encoding='utf-8')

            item2 = Path(tmpdir) / "item_002"
            item2.mkdir()
            # No mashup.pq

            other = Path(tmpdir) / "other_dir"
            other.mkdir()
            (other / "mashup.pq").write_text("query", encoding='utf-8')

            items = find_dataflow_items(Path(tmpdir))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].name, "item_001")

    def test_nonexistent_path(self):
        items = find_dataflow_items(Path("/nonexistent/xyz"))
        self.assertEqual(items, [])


class TestReadItemMapping(unittest.TestCase):
    def test_reads_pipe_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = Path(tmpdir) / "item_mapping.txt"
            mapping.write_text(
                "item_001 | WorkspaceID: ws1 | ItemID: id1 | Name: Test | Type: Dataflow | File: test.json\n",
                encoding='utf-8'
            )
            result = read_item_mapping(Path(tmpdir))
            self.assertEqual(result['item_001'], 'test.json')

    def test_reads_arrow_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping = Path(tmpdir) / "item_mapping.txt"
            mapping.write_text("item_001 -> test.json\n", encoding='utf-8')
            result = read_item_mapping(Path(tmpdir))
            self.assertEqual(result['item_001'], 'test.json')

    def test_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = read_item_mapping(Path(tmpdir))
            self.assertEqual(result, {})


class TestCreatePqtzipAndArchive(unittest.TestCase):
    def _create_item(self, tmpdir, name="item_001"):
        item = Path(tmpdir) / name
        item.mkdir()
        (item / "mashup.pq").write_text("let Source = 1 in Source", encoding='utf-8')
        (item / "queryMetadata.json").write_text(
            json.dumps({"queriesMetadata": {"Q1": {"isHidden": False}}}),
            encoding='utf-8'
        )
        (item / ".platform").write_text(
            json.dumps({"config": {"displayName": "TestFlow"}}),
            encoding='utf-8'
        )
        return item

    def test_creates_all_four_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            item = self._create_item(tmpdir)
            result = create_pqtzip_structure(item)

            self.assertTrue(result)
            pqtzip = item / "pqtzip"
            self.assertTrue((pqtzip / "MashupDocument.pq").exists())
            self.assertTrue((pqtzip / "MashupMetadata.json").exists())
            self.assertTrue((pqtzip / "Metadata.json").exists())
            self.assertTrue((pqtzip / "[Content_Types].xml").exists())

    def test_creates_defaults_when_metadata_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            item = Path(tmpdir) / "item_001"
            item.mkdir()
            (item / "mashup.pq").write_text("query", encoding='utf-8')

            result = create_pqtzip_structure(item)
            self.assertTrue(result)
            pqtzip = item / "pqtzip"
            self.assertTrue((pqtzip / "MashupMetadata.json").exists())
            self.assertTrue((pqtzip / "Metadata.json").exists())

            # Verify defaults are valid JSON
            meta = json.loads((pqtzip / "MashupMetadata.json").read_text(encoding='utf-8'))
            self.assertEqual(meta['QueriesMetadata'], [])
            md = json.loads((pqtzip / "Metadata.json").read_text(encoding='utf-8'))
            self.assertEqual(md['Name'], 'item_001')

    def test_creates_valid_pqt_archive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            item = self._create_item(tmpdir)
            create_pqtzip_structure(item)
            result = create_pqt_archive(item)

            self.assertTrue(result)
            pqt_file = item / "item_001.pqt"
            self.assertTrue(pqt_file.exists())

            with zipfile.ZipFile(pqt_file, 'r') as zf:
                names = zf.namelist()
                self.assertIn("MashupDocument.pq", names)
                self.assertIn("MashupMetadata.json", names)
                self.assertIn("Metadata.json", names)
                self.assertIn("[Content_Types].xml", names)
                self.assertEqual(len(names), 4)


class TestCopyDataflowItems(unittest.TestCase):
    def test_empty_list_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = copy_dataflow_items([], Path(tmpdir))
            self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
