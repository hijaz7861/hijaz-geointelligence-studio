import json
import tempfile
import unittest
from pathlib import Path
from app.editorial.script_validator import ProjectValidationError, release_blockers, validate_project, validate_project_file
from app.research.claim_ledger import add_claim
from app.research.source_ledger import add_source
SOURCE = {"title":"Fixture report","url":"https://example.org/report","published_at":"2026-10-20","source_type":"independent_reporting","claim_status":"independent_reporting","notes":"Fixture only."}
CLAIM = {"claim":"Example documentary statement","status":"independent_reporting","source_urls":[SOURCE["url"]],"notes":"Fixture only; not a factual claim."}
PROJECT = {"project_id":"fixture-001","title":"Test documentary","language":"en","target_duration_seconds":120,"script":"A test script, not for publication.","claim_ids":[CLAIM["claim"]],"media_assets":[{"asset_id":"asset-001","origin_url":SOURCE["url"],"rights_status":"licensed","notes":"Synthetic fixture."}],"approval":{"script_reviewed":True,"translation_reviewed":True,"media_rights_reviewed":True,"final_video_reviewed":True,"approved_by":"Test editor"}}
class ScriptValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.sources=self.root/"sources.json"; self.claims=self.root/"claims.json"; self.project=self.root/"project.json"
        add_source(SOURCE,self.sources); add_claim(CLAIM,self.claims,self.sources)
    def tearDown(self): self.tmp.cleanup()
    def test_valid_project(self): self.assertEqual(validate_project(PROJECT,[CLAIM],{SOURCE["url"]}),PROJECT)
    def test_unknown_claim_rejected(self):
        with self.assertRaisesRegex(ProjectValidationError,"absent from the claim ledger"): validate_project({**PROJECT,"claim_ids":["missing claim"]},[CLAIM],{SOURCE["url"]})
    def test_unknown_asset_origin_rejected(self):
        asset={**PROJECT["media_assets"][0],"origin_url":"https://example.net/unknown"}
        with self.assertRaisesRegex(ProjectValidationError,"not in source ledger"): validate_project({**PROJECT,"media_assets":[asset]},[CLAIM],{SOURCE["url"]})
    def test_invalid_duration_rejected(self):
        with self.assertRaisesRegex(ProjectValidationError,"positive integer"): validate_project({**PROJECT,"target_duration_seconds":True},[CLAIM],{SOURCE["url"]})
    def test_unsupported_language_rejected(self):
        with self.assertRaisesRegex(ProjectValidationError,"language must be"): validate_project({**PROJECT,"language":"xx"},[CLAIM],{SOURCE["url"]})
    def test_release_blockers_require_all_approvals(self): self.assertEqual(len(release_blockers({**PROJECT,"approval":{}},[CLAIM])),5)
    def test_unknown_media_rights_block_release(self):
        project={**PROJECT,"media_assets":[{**PROJECT["media_assets"][0],"rights_status":"unknown"}]}
        self.assertTrue(any("uncleared rights" in b for b in release_blockers(project,[CLAIM])))
    def test_file_loader_validates_project(self):
        self.project.write_text(json.dumps(PROJECT),encoding="utf-8")
        self.assertEqual(validate_project_file(self.project,self.claims,self.sources),PROJECT)
if __name__=="__main__": unittest.main()
