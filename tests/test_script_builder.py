import tempfile
import unittest
from pathlib import Path
from app.editorial.script_builder import ScriptBuildError, build_cited_draft, build_from_ledger
from app.research.claim_ledger import add_claim
from app.research.source_ledger import add_source
SOURCE={"title":"Fixture source","url":"https://example.org/fixture","published_at":"2026-10-20","source_type":"independent_reporting","claim_status":"independent_reporting","notes":"Synthetic test only."}
CLAIM={"claim":"A synthetic test statement","status":"independent_reporting","source_urls":[SOURCE["url"]],"notes":"Not a factual assertion."}
class ScriptBuilderTests(unittest.TestCase):
    def test_builds_cited_human_review_draft(self):
        draft=build_cited_draft([CLAIM],title="Fixture documentary")
        self.assertIn("[[claim:A synthetic test statement]]",draft)
        self.assertIn(SOURCE["url"],draft)
        self.assertIn("not publication-ready narration",draft)
    def test_rejects_empty_claims(self):
        with self.assertRaisesRegex(ScriptBuildError,"No claims"):
            build_cited_draft([],title="Empty")
    def test_rejects_unknown_language(self):
        with self.assertRaisesRegex(ScriptBuildError,"language must be"):
            build_cited_draft([CLAIM],title="Fixture",language="xx")
    def test_builds_from_ledger_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); sources=root/'sources.json'; claims=root/'claims.json'
            add_source(SOURCE,sources); add_claim(CLAIM,claims,sources)
            draft=build_from_ledger(title="Fixture",claims_path=claims,source_path=sources)
            self.assertIn("[[claim:A synthetic test statement]]",draft)
            self.assertIn(SOURCE["url"],draft)
if __name__=='__main__': unittest.main()
