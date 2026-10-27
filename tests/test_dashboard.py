import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from threading import Thread
from app.dashboard.server import build_status, create_server, render_dashboard_html
from app.research.source_ledger import add_source
from app.research.claim_ledger import add_claim
SOURCE={"title":"Fixture source","url":"https://example.org/fixture","published_at":"2026-10-20","source_type":"independent_reporting","claim_status":"independent_reporting","notes":"Synthetic test only."}
CLAIM={"claim":"Synthetic dashboard claim","status":"independent_reporting","source_urls":[SOURCE['url']],"notes":"Fixture only."}
PROJECT={"project_id":"dash-test","title":"Dashboard fixture <script>","language":"en","target_duration_seconds":60,"script":"[[claim:Synthetic dashboard claim]] Synthetic dashboard claim.","claim_ids":[CLAIM['claim']],"media_assets":[],"approval":{"script_reviewed":False,"translation_reviewed":False,"media_rights_reviewed":False,"final_video_reviewed":False,"approved_by":""}}
class DashboardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.sources=self.root/'sources.json'; self.claims=self.root/'claims.json'; self.project=self.root/'project.json'
  add_source(SOURCE,self.sources); add_claim(CLAIM,self.claims,self.sources); self.project.write_text(json.dumps(PROJECT),encoding='utf-8')
 def tearDown(self): self.tmp.cleanup()
 def test_status_shows_blocked_project(self):
  status=build_status(self.project,self.sources,self.claims)
  self.assertEqual(status['structural_validation'],'PASS'); self.assertFalse(status['publish_ready']); self.assertGreater(len(status['release_blockers']),0)
 def test_html_escapes_project_title(self):
  html=render_dashboard_html(build_status(self.project,self.sources,self.claims))
  self.assertNotIn('<script>',html); self.assertIn('&lt;script&gt;',html)
 def test_dashboard_serves_status_and_html_and_rejects_unknown_path(self):
  server=create_server('127.0.0.1',0,self.project,self.sources,self.claims); thread=Thread(target=server.serve_forever,daemon=True); thread.start()
  try:
   base=f'http://127.0.0.1:{server.server_address[1]}'
   with urlopen(base+'/api/status',timeout=2) as response:
    payload=json.loads(response.read()); self.assertEqual(payload['status'],'PASS'); self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
   with urlopen(base+'/',timeout=2) as response: self.assertIn(b'Read-only local status dashboard',response.read())
   with self.assertRaises(HTTPError): urlopen(base+'/unknown',timeout=2)
   request=Request(base+'/',data=b'{}',method='POST')
   with self.assertRaises(HTTPError) as caught: urlopen(request,timeout=2)
   self.assertEqual(caught.exception.code,405)
  finally: server.shutdown(); server.server_close(); thread.join(timeout=2)
 def test_refuses_non_loopback_binding(self):
  with self.assertRaisesRegex(ValueError,'loopback only'): create_server('0.0.0.0',8765)
if __name__=='__main__': unittest.main()
