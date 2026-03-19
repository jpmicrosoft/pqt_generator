"""Tests for shared_utils module."""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_utils import parse_ws_filename, parse_mapping_line, format_mapping_line, PQT_VERSION, CONTENT_TYPES_XML


class TestParseWsFilename(unittest.TestCase):
    def test_valid_standard_filename(self):
        result = parse_ws_filename("WS__abc123__def456__MyDataflow__Dataflow.json")
        self.assertEqual(result['workspace_id'], 'abc123')
        self.assertEqual(result['item_id'], 'def456')
        self.assertEqual(result['name'], 'MyDataflow')
        self.assertEqual(result['type'], 'Dataflow')

    def test_display_name_with_double_underscores(self):
        result = parse_ws_filename("WS__abc__def__Sales__Q1__Dataflow.json")
        self.assertEqual(result['name'], 'Sales__Q1')
        self.assertEqual(result['type'], 'Dataflow')

    def test_too_few_parts(self):
        self.assertIsNone(parse_ws_filename("WS__abc__def.json"))

    def test_missing_ws_prefix(self):
        self.assertIsNone(parse_ws_filename("XX__abc__def__name__type.json"))

    def test_no_extension(self):
        result = parse_ws_filename("WS__abc__def__name__type")
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'name')

    def test_empty_string(self):
        self.assertIsNone(parse_ws_filename(""))

    def test_guid_format_ids(self):
        result = parse_ws_filename(
            "WS__aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee__11111111-2222-3333-4444-555555555555__FinanceRun__Dataflow.json"
        )
        self.assertEqual(result['workspace_id'], 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')
        self.assertEqual(result['name'], 'FinanceRun')


class TestParseMappingLine(unittest.TestCase):
    def test_pipe_format(self):
        line = "item_001 | WorkspaceID: abc | ItemID: def | Name: Test | Type: Dataflow | File: test.json"
        result = parse_mapping_line(line)
        self.assertEqual(result['item_id'], 'item_001')
        self.assertEqual(result['File'], 'test.json')
        self.assertEqual(result['WorkspaceID'], 'abc')

    def test_arrow_format(self):
        result = parse_mapping_line("item_002 -> somefile.json")
        self.assertEqual(result['item_id'], 'item_002')
        self.assertEqual(result['File'], 'somefile.json')

    def test_empty_line(self):
        self.assertIsNone(parse_mapping_line(""))
        self.assertIsNone(parse_mapping_line("   "))

    def test_malformed_line(self):
        self.assertIsNone(parse_mapping_line("no_delimiters_here"))


class TestFormatMappingLine(unittest.TestCase):
    def test_with_metadata(self):
        metadata = {'workspace_id': 'ws1', 'item_id': 'it1', 'name': 'Test', 'type': 'Dataflow'}
        line = format_mapping_line('item_001', metadata, 'test.json')
        self.assertIn('WorkspaceID: ws1', line)
        self.assertIn('File: test.json', line)
        self.assertTrue(line.endswith('\n'))

    def test_without_metadata(self):
        line = format_mapping_line('item_001', None, 'test.json')
        self.assertEqual(line, 'item_001 -> test.json\n')


class TestConstants(unittest.TestCase):
    def test_pqt_version(self):
        self.assertEqual(PQT_VERSION, "1.0.0.0")

    def test_content_types_xml_structure(self):
        self.assertIn('<?xml version="1.0"', CONTENT_TYPES_XML)
        self.assertIn('Extension="json"', CONTENT_TYPES_XML)
        self.assertIn('Extension="pq"', CONTENT_TYPES_XML)


if __name__ == '__main__':
    unittest.main()
