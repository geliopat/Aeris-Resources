import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from validate_catalog import validate


class CatalogTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.catalog = self.root / "catalog.json"
        resource = self.root / "geodata" / "sample.txt"
        resource.parent.mkdir()
        resource.write_bytes(b"synthetic resource")
        self.entry = {
            "path": "geodata/sample.txt",
            "sha256": hashlib.sha256(b"synthetic resource").hexdigest(),
            "source": "https://example.invalid/sample",
            "revision": "fixture",
            "license": "fixture",
            "compatibility": "fixture",
        }

    def write_catalog(self, entries, version=1):
        self.catalog.write_text(
            json.dumps({"schema_version": version, "resources": entries}),
            encoding="utf-8",
        )

    def test_empty_and_valid_catalog(self):
        self.write_catalog([])
        self.assertEqual(validate(self.root), 0)
        self.write_catalog([self.entry])
        self.assertEqual(validate(self.root), 1)

    def test_rejects_wrong_json_shapes_and_versions(self):
        for value, message in (
            ([], "Invalid catalog object"),
            ({"schema_version": True, "resources": []}, "Invalid catalog schema version"),
            ({"schema_version": 1, "resources": {}}, "Invalid resource list"),
            ({"schema_version": 1, "resources": ["invalid"]}, "Entry 1 must be an object"),
        ):
            with self.subTest(value=value):
                self.catalog.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    validate(self.root)

    def test_rejects_duplicate_keys_and_nonstandard_json_constants(self):
        for contents, message in (
            ('{"schema_version":2,"schema_version":1,"resources":[]}', "Duplicate catalog key"),
            ('{"schema_version":1,"resources":[{"path":"a","path":"b"}]}', "Duplicate catalog key"),
            ('{"schema_version":1,"resources":[],"extra":NaN}', "Invalid JSON constant"),
            ('{"schema_version":1,', "Invalid catalog JSON"),
        ):
            with self.subTest(contents=contents):
                self.catalog.write_text(contents, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    validate(self.root)

    def test_rejects_malformed_or_incorrect_sha256(self):
        for digest, message in (("0" * 63, "Invalid SHA-256"), ("0" * 64, "Hash mismatch")):
            with self.subTest(digest=digest):
                self.write_catalog([dict(self.entry, sha256=digest)])
                with self.assertRaisesRegex(ValueError, message):
                    validate(self.root)

    def test_rejects_missing_file_and_duplicate_path(self):
        self.write_catalog([dict(self.entry, path="geodata/missing.txt")])
        with self.assertRaisesRegex(ValueError, "Resource file does not exist"):
            validate(self.root)
        self.write_catalog([self.entry, self.entry])
        with self.assertRaisesRegex(ValueError, "Duplicate resource path"):
            validate(self.root)

    def test_rejects_unsafe_or_nonportable_paths(self):
        for path in (
            "/geodata/sample.txt",
            "geodata/../geodata/sample.txt",
            "geodata//sample.txt",
            "geodata\\sample.txt",
            "C:/geodata/sample.txt",
            "geodata/sample.txt:other",
            "geodata/NUL.txt",
            "geodata/sample.txt.",
        ):
            with self.subTest(path=path):
                self.write_catalog([dict(self.entry, path=path)])
                with self.assertRaisesRegex(ValueError, "Invalid resource path"):
                    validate(self.root)

    def test_rejects_links_in_file_or_directory_positions(self):
        try:
            (self.root / "linked").symlink_to(self.root / "geodata", target_is_directory=True)
            (self.root / "alias.txt").symlink_to(self.root / self.entry["path"])
        except OSError as error:
            self.skipTest(f"Cannot create symlinks in this environment: {error.strerror}")
        for path in ("linked/sample.txt", "alias.txt"):
            with self.subTest(path=path):
                self.write_catalog([dict(self.entry, path=path)])
                with self.assertRaisesRegex(ValueError, "Resource path contains a link"):
                    validate(self.root)

    def test_rejects_linked_catalog(self):
        (self.root / "manifest-copy.json").write_text(
            '{"schema_version":1,"resources":[]}', encoding="utf-8"
        )
        try:
            self.catalog.symlink_to(self.root / "manifest-copy.json")
        except OSError as error:
            self.skipTest(f"Cannot create symlinks in this environment: {error.strerror}")
        with self.assertRaisesRegex(ValueError, "Resource path contains a link"):
            validate(self.root)
