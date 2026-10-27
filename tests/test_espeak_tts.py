import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from app.voice.espeak_tts import NarrationError, generate_narration
class EspeakTtsTests(unittest.TestCase):
 def setUp(self): self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name); self.out=self.root/'narration.wav'
 def tearDown(self): self.temp.cleanup()
 def test_rejects_empty_text(self):
  with self.assertRaisesRegex(NarrationError,'non-empty'): generate_narration('  ','en',self.out)
 def test_rejects_unsupported_language(self):
  with self.assertRaisesRegex(NarrationError,'language must'): generate_narration('Hello','xx',self.out)
 def test_rejects_non_wav_output(self):
  with self.assertRaisesRegex(NarrationError,r'\.wav extension'): generate_narration('Hello','en',self.root/'out.mp3')
 @patch('app.voice.espeak_tts.shutil.which',return_value='/usr/bin/espeak')
 @patch('app.voice.espeak_tts.subprocess.run')
 def test_reports_unavailable_language_without_fallback(self,run,which):
  run.return_value=Mock(returncode=0,stdout='Pty Language Age/Gender VoiceName File\n 5 en M default default\n',stderr='')
  with self.assertRaisesRegex(NarrationError,"voice 'ur' is not installed"):
   generate_narration('اردو متن','ur',self.out)
 @patch('app.voice.espeak_tts.shutil.which',return_value='/usr/bin/espeak')
 @patch('app.voice.espeak_tts.subprocess.run')
 def test_generates_transactionally_and_uses_stdin(self,run,which):
  def fake_run(command,**kwargs):
   if command[1]=='--voices': return Mock(returncode=0,stdout='Pty Language Age/Gender VoiceName File\n 5 en M default default\n',stderr='')
   Path(command[command.index('-w')+1]).write_bytes(b'RIFF'+b'0'*50)
   return Mock(returncode=0,stdout='',stderr='')
  run.side_effect=fake_run
  result=generate_narration('Hello world','en',self.out)
  self.assertEqual(result,self.out.resolve()); self.assertGreater(result.stat().st_size,44)
  self.assertTrue(any(call.kwargs.get('input')=='Hello world' for call in run.call_args_list))
  self.assertEqual(list(self.root.glob('.narration.*.wav')),[])
 @patch('app.voice.espeak_tts.shutil.which',return_value='/usr/bin/espeak')
 @patch('app.voice.espeak_tts.subprocess.run')
 def test_preserves_existing_output_on_failure(self,run,which):
  self.out.write_bytes(b'original')
  run.side_effect=[Mock(returncode=0,stdout='Pty Language Age/Gender VoiceName File\n 5 en M default default\n',stderr=''),Mock(returncode=1,stdout='',stderr='failed')]
  with self.assertRaisesRegex(NarrationError,'failed'): generate_narration('Hello','en',self.out,overwrite=True)
  self.assertEqual(self.out.read_bytes(),b'original')
if __name__=='__main__': unittest.main()
