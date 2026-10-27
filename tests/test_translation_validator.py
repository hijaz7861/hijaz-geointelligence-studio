import unittest
from app.editorial.translation_validator import TranslationValidationError, validate_translation
SOURCE="""# Sample

[[claim:Exact source claim]] A statement.

[EDITORIAL] Source: https://example.org/report
"""
class TranslationValidatorTests(unittest.TestCase):
 def test_accepts_preserved_markers_and_urls(self):
  result=validate_translation(SOURCE,"# نمونہ\n\n[[claim:Exact source claim]] ایک بیان۔\n\n[EDITORIAL] Source: https://example.org/report\n",language='ur')
  self.assertEqual(result['validation'],'PASS'); self.assertEqual(result['claim_marker_count'],1)
 def test_rejects_missing_claim_marker(self):
  with self.assertRaisesRegex(TranslationValidationError,'Claim markers changed'):
   validate_translation(SOURCE,SOURCE.replace('[[claim:Exact source claim]] ',''),language='ru')
 def test_rejects_added_claim_marker(self):
  with self.assertRaisesRegex(TranslationValidationError,'Claim markers changed'):
   validate_translation(SOURCE,SOURCE.replace('A statement.','[[claim:Invented claim]] Another statement.'),language='zh')
 def test_rejects_missing_url(self):
  with self.assertRaisesRegex(TranslationValidationError,'Source URLs must be preserved'):
   validate_translation(SOURCE,SOURCE.replace('https://example.org/report',''),language='en')
 def test_rejects_reordered_markers(self):
  source='[[claim:first]] A.\n\n[[claim:second]] B.'
  translated='[[claim:second]] B.\n\n[[claim:first]] A.'
  with self.assertRaisesRegex(TranslationValidationError,'order changed'):
   validate_translation(source,translated,language='ru')
 def test_rejects_empty_translation(self):
  with self.assertRaisesRegex(TranslationValidationError,'Translated script must be non-empty'):
   validate_translation(SOURCE,' ',language='zh')
 def test_rejects_unknown_language(self):
  with self.assertRaisesRegex(TranslationValidationError,'language must be'):
   validate_translation(SOURCE,SOURCE,language='xx')
if __name__=='__main__': unittest.main()
