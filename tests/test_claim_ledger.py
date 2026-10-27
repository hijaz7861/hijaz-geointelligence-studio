import json
import tempfile
import unittest
from pathlib import Path
from app.research.claim_ledger import ClaimLedgerError, add_claim, load_claims, validate_claim
from app.research.source_ledger import add_source
SOURCE = {"title":"Example public report","url":"https://example.org/report","published_at":"2026-10-20","source_type":"independent_reporting","claim_status":"independent_reporting","notes":"Fixture only."}
CLAIM = {"claim":"Example claim for tests","status":"independent_reporting","source_urls":[SOURCE["url"]],"notes":"Fixture only; not a factual claim."}
class ClaimLedgerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.sources=self.root/"sources.json"; self.claims=self.root/"claims.json"; add_source(SOURCE,self.sources)
 def tearDown(self): self.tmp.cleanup()
 def test_add_and_reload_claim_with_known_source(self):
  add_claim(CLAIM,self.claims,self.sources); self.assertEqual(load_claims(self.claims,self.sources),[CLAIM])
 def test_rejects_missing_source_url(self):
  with self.assertRaisesRegex(ClaimLedgerError,"non-empty JSON array"): validate_claim({**CLAIM,"source_urls":[]})
 def test_rejects_unknown_source_url(self):
  with self.assertRaisesRegex(ClaimLedgerError,"absent from the source ledger"): add_claim({**CLAIM,"source_urls":["https://example.net/not-recorded"]},self.claims,self.sources)
 def test_rejects_invalid_status(self):
  with self.assertRaisesRegex(ClaimLedgerError,"Unsupported claim status"): validate_claim({**CLAIM,"status":"AI_confirmed"})
 def test_rejects_duplicate_claim_case_insensitively(self):
  add_claim(CLAIM,self.claims,self.sources)
  with self.assertRaisesRegex(ClaimLedgerError,"Duplicate claim text"): add_claim({**CLAIM,"claim":CLAIM["claim"].upper()},self.claims,self.sources)
 def test_rejects_duplicate_urls_in_claim(self):
  with self.assertRaisesRegex(ClaimLedgerError,"Duplicate source URL"): validate_claim({**CLAIM,"source_urls":[SOURCE["url"],SOURCE["url"]]})
 def test_reports_corrupt_claim_json(self):
  self.claims.write_text("{broken",encoding="utf-8")
  with self.assertRaisesRegex(ClaimLedgerError,"Cannot read claim ledger"): load_claims(self.claims,self.sources)
 def test_rejects_non_array_claim_file(self):
  self.claims.write_text(json.dumps({}),encoding="utf-8")
  with self.assertRaisesRegex(ClaimLedgerError,"JSON array"): load_claims(self.claims,self.sources)
if __name__=="__main__": unittest.main()
