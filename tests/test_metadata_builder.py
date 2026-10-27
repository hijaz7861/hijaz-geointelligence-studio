import unittest
from app.publishing.metadata_builder import MetadataBuildError, build_metadata_package
SOURCE={"title":"Fixture source","url":"https://example.org/fixture","published_at":"2026-10-20","source_type":"independent_reporting","claim_status":"independent_reporting","notes":"Synthetic test only."}
CLAIM={"claim":"A synthetic test statement","status":"independent_reporting","source_urls":[SOURCE["url"]],"notes":"Not a factual assertion."}
def project():
 return {"project_id":"test","title":"Fixture documentary","language":"en","target_duration_seconds":60,"script":"[[claim:A synthetic test statement]] A synthetic test statement.","claim_ids":[CLAIM["claim"]],"media_assets":[],"approval":{"script_reviewed":False,"translation_reviewed":False,"media_rights_reviewed":False,"final_video_reviewed":False,"approved_by":""}}
class MetadataBuilderTests(unittest.TestCase):
 def test_builds_cited_metadata_but_never_marks_it_publish_ready(self):
  result=build_metadata_package(project(),[CLAIM],{SOURCE["url"]})
  self.assertEqual(result["release_status"],"draft_blocked"); self.assertFalse(result["publish_ready"])
  self.assertIn(SOURCE["url"],result["description"]); self.assertIn("human approval",result["description"])
 def test_rejects_uncited_script(self):
  with self.assertRaisesRegex(MetadataBuildError,"lacks a claim citation marker"):
   build_metadata_package({**project(),"script":"Unsupported sentence."},[CLAIM],{SOURCE["url"]})
if __name__=="__main__": unittest.main()
