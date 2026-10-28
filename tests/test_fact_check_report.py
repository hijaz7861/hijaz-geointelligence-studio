import unittest
from app.editorial.fact_check_report import build_fact_check_report

SOURCE = {"title": "Fixture report", "url": "https://news.example.org/a", "published_at": "2026-10-20", "source_type": "independent_reporting"}
CLAIM = {"claim": "Synthetic statement", "status": "unverified", "source_urls": [SOURCE["url"]], "notes": "fixture"}

class FactCheckReportTests(unittest.TestCase):
    def test_report_summarizes_status_and_source(self):
        report = build_fact_check_report([CLAIM], [SOURCE])
        self.assertIn("Claims reviewed: 1", report)
        self.assertIn("Claims labelled unverified: 1", report)
        self.assertIn("[Fixture report](https://news.example.org/a)", report)
        self.assertIn("Review warning (unverified)", report)
        self.assertIn("does not establish truth", report)

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
