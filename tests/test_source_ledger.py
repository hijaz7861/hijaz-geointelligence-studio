import json
import tempfile
import unittest
from pathlib import Path

from app.research.source_ledger import SourceLedgerError, add_source, canonicalize_http_url, load_sources, validate_source

VALID = {"title": "Example public report", "url": "https://example.org/report", "published_at": "2026-10-20",
         "source_type": "independent_reporting", "claim_status": "independent_reporting",
         "notes": "Example fixture only; not a factual claim."}


class SourceLedgerTests(unittest.TestCase):
    def test_valid_source_is_normalized(self):
        self.assertEqual(validate_source(VALID), VALID)

    def test_rejects_non_http_url(self):
        with self.assertRaises(SourceLedgerError):
            validate_source({**VALID, "url": "file:///etc/passwd"})

    def test_rejects_malformed_authority_and_embedded_credentials(self):
        invalid_urls = (
            "https://user:password@example.org/report",
            "https://example.org:not-a-port/report",
            "https://example.org:0/report",
            "https://example.org:/report",
            "https://[broken/report",
            "https://example.org\\\\path",
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(SourceLedgerError):
                    validate_source({**VALID, "url": url})

    def test_canonicalizes_idn_default_port_fragment_and_ipv6(self):
        self.assertEqual(
            canonicalize_http_url("HTTPS://BÜCHER.example:443/report#section"),
            "https://xn--bcher-kva.example/report",
        )
        self.assertEqual(
            canonicalize_http_url("https://[2001:0db8:0:0::1]:443/report/"),
            "https://[2001:db8::1]/report/",
        )

    def test_rejects_malformed_dns_hostname(self):
        for url in (
            "https://-bad.example/report",
            "https://bad_.example/report",
            "https://example..org/report",
        ):
            with self.subTest(url=url):
                with self.assertRaises(SourceLedgerError):
                    validate_source({**VALID, "url": url})

    def test_rejects_invalid_date(self):
        with self.assertRaises(SourceLedgerError):
            validate_source({**VALID, "published_at": "yesterday"})

    def test_rejects_compact_non_iso_date(self):
        with self.assertRaises(SourceLedgerError):
            validate_source({**VALID, "published_at": "20261020"})

    def test_rejects_impossible_calendar_date(self):
        with self.assertRaises(SourceLedgerError):
            validate_source({**VALID, "published_at": "2026-02-30"})

    def test_rejects_url_with_whitespace(self):
        with self.assertRaises(SourceLedgerError):
            validate_source({**VALID, "url": "https://example.org/a b"})

    def test_rejects_unknown_claim_status(self):
        with self.assertRaises(SourceLedgerError):
            validate_source({**VALID, "claim_status": "certain_because_ai_said_so"})

    def test_add_and_reload_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            add_source(VALID, path)
            self.assertEqual(load_sources(path), [VALID])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [VALID])

    def test_duplicate_url_is_rejected_case_default_port_and_fragment_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            add_source(VALID, path)
            with self.assertRaisesRegex(SourceLedgerError, "already exists"):
                add_source({**VALID, "url": "HTTPS://EXAMPLE.ORG:443/report#section"}, path)

    def test_path_trailing_slash_is_preserved_as_a_distinct_resource(self):
        self.assertNotEqual(
            canonicalize_http_url("https://example.org/report"),
            canonicalize_http_url("https://example.org/report/"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            add_source(VALID, path)
            add_source({**VALID, "url": "https://example.org/report/"}, path)
            self.assertEqual(len(load_sources(path)), 2)

    def test_empty_path_canonicalizes_to_root(self):
        self.assertEqual(canonicalize_http_url("HTTPS://EXAMPLE.ORG:443#top"), "https://example.org/")

    def test_missing_fields_are_rejected(self):
        with self.assertRaisesRegex(SourceLedgerError, "Missing required fields"):
            validate_source({"title": "Incomplete"})

    def test_corrupt_json_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaisesRegex(SourceLedgerError, "Cannot read source ledger"):
                load_sources(path)

    def test_non_array_ledger_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(SourceLedgerError, "JSON array"):
                load_sources(path)


if __name__ == "__main__":
    unittest.main()
