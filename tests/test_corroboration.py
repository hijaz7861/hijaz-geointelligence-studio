import unittest
from app.research.corroboration import assess_corroboration
CLAIM={"claim":"Synthetic statement","status":"independent_reporting","source_urls":["https://news.example.org/a"],"notes":"fixture"}
SOURCES=[{"url":"https://news.example.org/a","source_type":"independent_reporting"}]
class CorroborationTests(unittest.TestCase):
 def test_warns_for_single_independent_domain(self):
  warnings=assess_corroboration([CLAIM],SOURCES)
  self.assertEqual([w['code'] for w in warnings],['single_independent_domain'])
 def test_same_domain_does_not_count_as_independent_corroboration(self):
  claim={**CLAIM,'source_urls':['https://news.example.org/a','https://www.news.example.org/b']}
  sources=[*SOURCES,{"url":"https://www.news.example.org/b","source_type":"independent_reporting"}]
  self.assertEqual(assess_corroboration([claim],sources)[0]['code'],'single_independent_domain')
 def test_multiple_independent_domains_no_warning(self):
  claim={**CLAIM,'source_urls':['https://news.example.org/a','https://another.example.net/b']}
  sources=[*SOURCES,{"url":"https://another.example.net/b","source_type":"independent_reporting"}]
  self.assertEqual(assess_corroboration([claim],sources),[])
 def test_official_statement_alone_is_not_independent_reporting(self):
  source={"url":"https://gov.example.org/statement","source_type":"official_statement"}
  claim={**CLAIM,'source_urls':[source['url']]}
  self.assertEqual(assess_corroboration([claim],[source])[0]['code'],'no_independent_reporting')
 def test_unverified_claim_gets_explicit_warning(self):
  warnings=assess_corroboration([{**CLAIM,'status':'unverified'}],SOURCES)
  self.assertIn('unverified',[w['code'] for w in warnings])
if __name__=='__main__': unittest.main()
