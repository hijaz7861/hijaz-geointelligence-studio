import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.publishing.release_bundle import ReleaseBundleError, build_release_bundle, sha256_file, write_release_bundle
from app.research.source_ledger import add_source
from app.research.claim_ledger import add_claim
SOURCE={"title":"Synthetic report","url":"https://example.org/report","published_at":"2026-10-20","source_type":"independent_reporting","claim_status":"independent_reporting","notes":"Synthetic fixture only."}
CLAIM={"claim":"Synthetic documentary claim","status":"independent_reporting","source_urls":[SOURCE["url"]],"notes":"Fixture only."}
PROJECT={"project_id":"bundle-fixture","title":"Synthetic release fixture","language":"en","target_duration_seconds":60,"script":"[[claim:Synthetic documentary claim]] Synthetic documentary claim.","claim_ids":[CLAIM["claim"]],"media_assets":[{"asset_id":"asset-fixture","origin_url":SOURCE["url"],"rights_status":"unknown","creator":"Fixture","attribution":"Fixture","usage_scope":"Never publish","rights_evidence":"Fixture only","notes":"Synthetic test"}],"approval":{"script_reviewed":False,"translation_reviewed":False,"media_rights_reviewed":False,"final_video_reviewed":False,"approved_by":""}}
class ReleaseBundleTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name); self.sources=self.root/'sources.json'; self.claims=self.root/'claims.json'; self.project=self.root/'project.json'
  add_source(SOURCE,self.sources); add_claim(CLAIM,self.claims,self.sources); self.project.write_text(json.dumps(PROJECT),encoding='utf-8')
  self.video=self.root/'final.mp4'; self.video.write_bytes(b'synthetic video fixture')
  self.srt=self.root/'final.srt'; self.srt.write_text('1\n00:00:00,000 --> 00:00:01,000\nSynthetic caption.\n',encoding='utf-8')
  self.metadata=self.root/'metadata.json'; self.metadata.write_text(json.dumps({'publish_ready':False,'release_blockers':['Human approval missing']}),encoding='utf-8')
 def tearDown(self): self.temp.cleanup()
 @patch('app.publishing.release_bundle.inspect_rendered_video',return_value={'validation':'PASS','duration_seconds':1.0,'width':1280,'height':720})
 def test_bundle_hashes_inputs_and_never_marks_publish_ready(self,probe):
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims,render_path=self.video,subtitle_path=self.srt,metadata_path=self.metadata)
  self.assertEqual(bundle['structural_validation'],'PASS'); self.assertFalse(bundle['publish_ready']); self.assertEqual(bundle['render_validation']['validation'],'PASS')
  self.assertTrue(any('uncleared rights' in item for item in bundle['release_blockers']))
  project_entry=next(item for item in bundle['input_files'] if item['label']=='project')
  self.assertEqual(project_entry['sha256'],sha256_file(self.project))
  self.assertTrue(any('never grants permission' in item for item in bundle['release_blockers']))
 def test_missing_render_subtitle_and_metadata_are_blockers(self):
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims)
  self.assertTrue(any('rendered video is missing' in item.lower() for item in bundle['release_blockers']))
  self.assertTrue(any('subtitle file is missing' in item.lower() for item in bundle['release_blockers']))
  self.assertTrue(any('metadata draft is missing' in item.lower() for item in bundle['release_blockers']))
 def test_invalid_project_or_ledgers_fail_closed(self):
  self.project.write_text('{}',encoding='utf-8')
  with self.assertRaises(ReleaseBundleError): build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims)
 def test_output_refuses_overwrite_by_default(self):
  out=self.root/'bundle.json'; out.write_text('{}',encoding='utf-8')
  with self.assertRaisesRegex(ReleaseBundleError,'already exists'): write_release_bundle({'publish_ready':False},out)
 def test_output_writes_valid_json(self):
  out=self.root/'bundle.json'; result=write_release_bundle({'publish_ready':False,'release_blockers':['review']},out)
  self.assertEqual(json.loads(result.read_text())['publish_ready'],False)
if __name__=='__main__': unittest.main()
