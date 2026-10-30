import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.publishing.release_bundle import ReleaseBundleError, build_release_bundle, sha256_file, write_release_bundle
from app.research.source_ledger import add_source
from app.research.claim_ledger import add_claim
from app.publishing.approval_receipts import APPROVAL_STAGES, create_approval_key, record_approval
ROOT=Path(__file__).resolve().parents[1]
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
 @patch('app.publishing.release_bundle.inspect_rendered_video',return_value={'validation':'PASS','duration_seconds':1.0,'width':1280,'height':720,'audio_stream_count':1,'subtitle_stream_count':1,'audio_duration_seconds':1.0})
 def test_bundle_hashes_inputs_and_never_marks_publish_ready(self,probe):
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims,render_path=self.video,subtitle_path=self.srt,metadata_path=self.metadata)
  self.assertEqual(bundle['structural_validation'],'PASS'); self.assertFalse(bundle['publish_ready']); self.assertEqual(bundle['render_validation']['validation'],'PASS')
  self.assertTrue(any('uncleared rights' in item for item in bundle['release_blockers']))
  project_entry=next(item for item in bundle['input_files'] if item['label']=='project')
  self.assertEqual(project_entry['sha256'],sha256_file(self.project))
  self.assertTrue(any('never grants permission' in item for item in bundle['release_blockers']))
  probe.assert_called_once_with(self.video,require_audio=True,require_subtitles=True,min_width=1280,min_height=720)
  self.assertTrue(bundle['subtitle_validation']['timeline_within_render'])
 @patch('app.publishing.release_bundle.inspect_rendered_video',return_value={'validation':'PASS','duration_seconds':1.0,'width':1280,'height':720,'audio_stream_count':1,'subtitle_stream_count':1,'audio_duration_seconds':1.0})
 def test_subtitle_timeline_beyond_render_duration_is_blocked(self,probe):
  self.srt.write_text('1\n00:00:00,000 --> 00:00:02,000\nCaption extends past render.\n',encoding='utf-8')
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims,render_path=self.video,subtitle_path=self.srt,metadata_path=self.metadata)
  self.assertFalse(bundle['subtitle_validation']['timeline_within_render'])
  self.assertTrue(any('Subtitle timeline exceeds rendered video duration by 1000 ms.' in item for item in bundle['release_blockers']))
 @patch('app.publishing.release_bundle.inspect_rendered_video',return_value={'validation':'PASS','duration_seconds':2.0,'width':1280,'height':720,'audio_stream_count':1,'subtitle_stream_count':1,'audio_duration_seconds':0.5})
 def test_subtitle_timeline_beyond_audio_duration_is_blocked(self,probe):
  self.srt.write_text('1\\n00:00:00,000 --> 00:00:01,000\\nCaption extends beyond audio.\\n',encoding='utf-8')
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims,render_path=self.video,subtitle_path=self.srt,metadata_path=self.metadata)
  self.assertFalse(bundle['subtitle_validation']['timeline_within_audio'])
  self.assertTrue(any('Subtitle timeline exceeds audio stream duration by 500 ms.' in item for item in bundle['release_blockers']))

 def test_approval_receipts_are_required_and_reported(self):
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims)
  self.assertEqual(bundle['human_approval_record']['receipt_validation']['validation'],'NOT_VERIFIED')
  self.assertTrue(any('Tamper-evident human approval receipts' in item for item in bundle['release_blockers']))

 @patch('app.publishing.release_bundle.inspect_rendered_video',return_value={'validation':'PASS','duration_seconds':1.0,'width':1280,'height':720,'audio_stream_count':1,'subtitle_stream_count':1,'audio_duration_seconds':1.0})
 def test_valid_approval_receipts_are_included_but_never_authorize_publish(self,probe):
  project={**PROJECT,'approval':{'script_reviewed':True,'translation_reviewed':True,'media_rights_reviewed':True,'final_video_reviewed':True,'approved_by':'Human reviewer'}}
  self.project.write_text(json.dumps(project),encoding='utf-8')
  key=create_approval_key(self.root/'private'/'approval.key')
  receipts=self.root/'approval-receipts.json'
  for stage in APPROVAL_STAGES:
   record_approval(self.project,receipts,key,stage=stage,decision='approved',reviewer='Human reviewer',reason='Reviewed the relevant project materials.',artifact_path=self.video if stage=='final_video_reviewed' else None,reviewed_at='2026-10-30T03:00:00Z')
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims,render_path=self.video,subtitle_path=self.srt,metadata_path=self.metadata,approval_receipts_path=receipts,approval_key_path=key)
  self.assertEqual(bundle['human_approval_record']['receipt_validation']['validation'],'PASS')
  self.assertFalse(bundle['publish_ready'])
  self.assertTrue(any('never grants permission' in item for item in bundle['release_blockers']))

 def test_missing_render_subtitle_and_metadata_are_blockers(self):
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims)
  self.assertTrue(any('rendered video is missing' in item.lower() for item in bundle['release_blockers']))
  self.assertTrue(any('subtitle file is missing' in item.lower() for item in bundle['release_blockers']))
  self.assertTrue(any('metadata draft is missing' in item.lower() for item in bundle['release_blockers']))
 def test_placeholder_license_evidence_is_a_blocker(self):
  project={**PROJECT,"media_assets":[{**PROJECT["media_assets"][0],"rights_status":"licensed","rights_evidence":"Synthetic fixture evidence, not a real license"}]}
  self.project.write_text(json.dumps(project),encoding='utf-8')
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims)
  self.assertTrue(any('placeholder or requires manual verification' in item for item in bundle['release_blockers']))
 def test_original_media_with_placeholder_rights_evidence_is_a_blocker(self):
  project={**PROJECT,"media_assets":[{**PROJECT["media_assets"][0],"rights_status":"original","rights_evidence":"Fixture only"}]}
  self.project.write_text(json.dumps(project),encoding='utf-8')
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims)
  self.assertTrue(any('placeholder or requires manual verification' in item for item in bundle['release_blockers']))
 def test_non_object_metadata_is_a_blocker_not_a_crash(self):
  self.metadata.write_text('[]',encoding='utf-8')
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims,metadata_path=self.metadata)
  self.assertTrue(any('Metadata draft must be a JSON object' in item for item in bundle['release_blockers']))
 def test_invalid_utf8_metadata_is_a_blocker_not_a_crash(self):
  self.metadata.write_bytes(b'\xff\xfe{broken')
  bundle=build_release_bundle(self.project,source_path=self.sources,claims_path=self.claims,metadata_path=self.metadata)
  self.assertTrue(any('Metadata draft is unreadable JSON/UTF-8' in item for item in bundle['release_blockers']))
 def test_cli_refuses_output_path_that_matches_input(self):
  result=subprocess.run([sys.executable,str(ROOT/'scripts'/'build_release_bundle.py'),'--project',str(self.project),'--sources-file',str(self.sources),'--claims-file',str(self.claims),'--output',str(self.project)],capture_output=True,text=True)
  self.assertEqual(result.returncode,2)
  self.assertIn('must not overwrite',result.stderr)
  default_claims=ROOT/'data'/'sources'/'claims.json'
  second=subprocess.run([sys.executable,str(ROOT/'scripts'/'build_release_bundle.py'),'--project',str(self.project),'--sources-file',str(self.sources),'--output',str(default_claims)],capture_output=True,text=True)
  self.assertEqual(second.returncode,2)
  self.assertIn('must not overwrite',second.stderr)
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
