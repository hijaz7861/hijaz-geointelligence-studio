import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.research.feed_importer import FeedImportError, _validate_feed_url, load_feed_config, parse_feed_items, import_feeds
from app.research.source_ledger import load_sources
RSS=b'''<?xml version="1.0"?><rss version="2.0"><channel><item><title>Example story</title><link>https://news.example.org/story</link><pubDate>Tue, 20 Oct 2026 10:00:00 GMT</pubDate><description>Fixture only</description></item></channel></rss>'''
ATOM=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom story</title><link href="https://news.example.org/atom"/><published>2026-10-20T10:00:00Z</published></entry></feed>'''
class FeedImporterTests(unittest.TestCase):
 def test_parses_rss_metadata(self):
  items=parse_feed_items(RSS); self.assertEqual(items[0]['published_at'],'2026-10-20'); self.assertEqual(items[0]['title'],'Example story')
 def test_parses_atom_metadata(self): self.assertEqual(parse_feed_items(ATOM)[0]['url'],'https://news.example.org/atom')
 def test_rejects_malformed_xml(self):
  with self.assertRaisesRegex(FeedImportError,'malformed'): parse_feed_items(b'<broken')
 def test_rejects_doctype_and_entity_declarations(self):
  with self.assertRaisesRegex(FeedImportError,'entities'): parse_feed_items(b'<!DOCTYPE x [<!ENTITY e "bad">]><rss/>')
 def test_rejects_http_and_credentials(self):
  with self.assertRaisesRegex(FeedImportError,'HTTPS'): _validate_feed_url('http://news.example.org/rss')
  with self.assertRaisesRegex(FeedImportError,'credentials'): _validate_feed_url('https://user:pass@news.example.org/rss')
  with self.assertRaisesRegex(FeedImportError,'invalid port'): _validate_feed_url('https://news.example.org:bad/rss')
 def test_rejects_local_hosts(self):
  with self.assertRaisesRegex(FeedImportError,'Local or internal'): _validate_feed_url('https://localhost/rss')
 def test_loads_config_and_rejects_bad_type(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'feeds.json'; p.write_text(json.dumps({'feeds':[{'name':'Fixture','url':'https://news.example.org/rss'}]}),encoding='utf-8')
   with patch('app.research.feed_importer.socket.getaddrinfo',return_value=[(2,1,6,'',('93.184.216.34',443))]): self.assertEqual(load_feed_config(p)[0]['name'],'Fixture')
   p.write_text(json.dumps({'feeds':[{'name':'Fixture','url':'https://news.example.org/rss','source_type':'unknown'}]}),encoding='utf-8')
   with patch('app.research.feed_importer.socket.getaddrinfo',return_value=[(2,1,6,'',('93.184.216.34',443))]):
    with self.assertRaisesRegex(FeedImportError,'source_type'): load_feed_config(p)
 def test_blocks_private_dns_resolution(self):
  with patch('app.research.feed_importer.socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
   with self.assertRaisesRegex(FeedImportError,'non-public IP'): _validate_feed_url('https://news.example.org/rss')
 def test_imports_feed_items_into_source_ledger_and_skips_duplicates(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp); config=root/'feeds.json'; ledger=root/'sources.json'
   config.write_text(json.dumps({'feeds':[{'name':'Fixture feed','url':'https://news.example.org/rss'}]}),encoding='utf-8')
   with patch('app.research.feed_importer.socket.getaddrinfo',return_value=[(2,1,6,'',('93.184.216.34',443))]), patch('app.research.feed_importer._fetch_feed',return_value=RSS):
    first=import_feeds(config,ledger); second=import_feeds(config,ledger)
   self.assertEqual(first['sources_added'],1); self.assertEqual(second['items_skipped'],1)
   self.assertIn('not been independently verified',load_sources(ledger)[0]['notes'])
if __name__=='__main__': unittest.main()
