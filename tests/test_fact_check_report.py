import unittest
from app.editorial.fact_check_report import build_fact_check_report

SOURCE = {"title": "Fixture report", "url": "https://news.example.org/a", "published_at": "2026-10-20", "source_type": "independent_reporting"}
CLAIM = {"claim": "Synthetic statement", "status": "unverified", "source_urls": [SOURCE["url"]], "notes": "fixture"}

class FactCheckReportTests(unittest.TestCase):
    def test_report_summarizes_status_and_source(self):
        report = build_fact_check_report([CLAIM], [SOURCE])
        self.assertIn("Claims reviewed: 1", report)
        self.assertIn("Claims labelled unverified: 1", report)
        self.assertIn('<a href="https://news.example.org/a">Fixture report</a>', report)
        self.assertIn("Review warning (unverified)", report)
        self.assertIn("does not establish truth", report)

    def test_escapes_untrusted_claim_and_source_metadata(self):
        source = {**SOURCE, "title": '<img src=x onerror="alert(1)">' }
        claim = {**CLAIM, "claim": "<script>alert(1)</script>", "source_urls": [SOURCE["url"]]}
        report = build_fact_check_report([claim], [source])
        self.assertNotIn("<script>", report)
        self.assertNotIn("<img", report)
        self.assertIn("&lt;script&gt;", report)
        self.assertIn("&lt;img", report)

    def test_never_links_non_http_source_urls(self):
        bad = {**SOURCE, "url": "javascript:alert(1)"}
        claim = {**CLAIM, "source_urls": [bad["url"]]}
        report = build_fact_check_report([claim], [bad])
        self.assertNotIn('href="javascript:', report)
        self.assertIn("javascript:alert(1)", report)

    def test_non_string_source_reference_does_not_crash_report(self):
        claim = {**CLAIM, "source_urls": [{"unexpected": "object"}]}
        report = build_fact_check_report([claim], [SOURCE])
        self.assertIn("Invalid non-text source reference", report)

    def test_empty_ledgers_are_explicit(self):
        report = build_fact_check_report([], [])
        self.assertIn("Claims reviewed: 0", report)
        self.assertIn("No claims are recorded", report)
        self.assertIn("Human review checklist", report)

    def test_claim_without_independent_reporting_warns(self):
        official = {"title": "Official statement", "url": "https://gov.example.org/a", "published_at": "2026-10-20", "source_type": "official_statement"}
        claim = {**CLAIM, "status": "official_claim", "source_urls": [official["url"]]}
        report = build_fact_check_report([claim], [official])
        self.assertIn("Review warning (no_independent_reporting)", report)

if __name__ == "__main__":
    unittest.main()
