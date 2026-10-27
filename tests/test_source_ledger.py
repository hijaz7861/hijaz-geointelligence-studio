import json
import tempfile
import unittest
from pathlib import Path

from app.research.source_ledger import SourceLedgerError, add_source, load_sources, validate_source

VALID = {
    "title": "Example public report",
    "url": "https://example.org/report",
    "published_at": "2026-10-20",
    "source_type": "independent_reporting",
    "claim_status": "independent_reporting",
    "notes": "Example fixture only; not a factual claim.",
}


class SourceLedgerTests(unittest.TestCase):
    def test_valid_source_is_normalized(self):
        self.assertEqual(validate_source(VALID), VALID)

    def test_rejects_non_http_url(self):
        source = {**VALID, "url": "file:///etc/passwd"}
        with self.assertRaises(SourceLedgerError):
            validate_source(source)

    def test_rejects_invalid_date(self):
        source = {**VALID, "published_at": "yesterday"}
        with self.assertRaises(SourceLedgerError):
            validate_source(source)

    def test_rejects_unknown_claim_status(self):
        source = {**VALID, "claim_status": "certain_because_ai_said_so"}
        with self.assertRaises(SourceLedgerError):
            validate_source(source)

    def test_add_and_reload_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            add_source(VALID, path)
            self.assertEqual(load_sources(path), [VALID])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [VALID])

    def test_duplicate_url_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            add_source(VALID, path)
            with self.assertRaisesRegex(SourceLedgerError, "already exists"):
                add_source(VALID, path)

    def test_missing_fields_are_rejected(self):
        with self.assertRaisesRegex(SourceLedgerError, "Missing required fields"):
            validate_source({"title": "Incomplete"})


if __name__ == "__main__":
    unittest.main()
