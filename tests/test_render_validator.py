import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from app.video.render_validator import RenderValidationError, inspect_rendered_video
PROBE={'streams':[{'codec_type':'video','codec_name':'h264','width':1920,'height':1080},{'codec_type':'audio','codec_name':'aac'},{'codec_type':'subtitle','codec_name':'mov_text'}],'format':{'duration':'12.5'}}
class RenderValidatorTests(unittest.TestCase):
 def setUp(self): self.temp=tempfile.TemporaryDirectory(); self.file=Path(self.temp.name)/'render.mp4'; self.file.write_bytes(b'fixture')
 def tearDown(self): self.temp.cleanup()
 @patch('app.video.render_validator.shutil.which',return_value='/usr/bin/ffprobe')
 @patch('app.video.render_validator.subprocess.run')
 def test_accepts_required_streams(self,run,which):
  run.return_value=Mock(returncode=0,stdout=json.dumps(PROBE),stderr='')
  result=inspect_rendered_video(self.file,require_subtitles=True,min_width=1280,min_height=720)
  self.assertEqual(result['validation'],'PASS'); self.assertEqual(result['subtitle_stream_count'],1)
 @patch('app.video.render_validator.shutil.which',return_value='/usr/bin/ffprobe')
 @patch('app.video.render_validator.subprocess.run')
 def test_rejects_missing_audio(self,run,which):
  run.return_value=Mock(returncode=0,stdout=json.dumps({'streams':[PROBE['streams'][0]],'format':{'duration':'12'}}),stderr='')
  with self.assertRaisesRegex(RenderValidationError,'no audio stream'): inspect_rendered_video(self.file)
 @patch('app.video.render_validator.shutil.which',return_value='/usr/bin/ffprobe')
 @patch('app.video.render_validator.subprocess.run')
 def test_rejects_missing_subtitles_when_required(self,run,which):
  run.return_value=Mock(returncode=0,stdout=json.dumps({'streams':PROBE['streams'][:2],'format':{'duration':'12'}}),stderr='')
  with self.assertRaisesRegex(RenderValidationError,'no subtitle stream'): inspect_rendered_video(self.file,require_subtitles=True)
 @patch('app.video.render_validator.shutil.which',return_value='/usr/bin/ffprobe')
 @patch('app.video.render_validator.subprocess.run')
 def test_rejects_low_resolution(self,run,which):
  data={**PROBE,'streams':[dict(PROBE['streams'][0],width=320,height=240),*PROBE['streams'][1:]]}
  run.return_value=Mock(returncode=0,stdout=json.dumps(data),stderr='')
  with self.assertRaisesRegex(RenderValidationError,'below required'): inspect_rendered_video(self.file,min_width=1280,min_height=720)
 @patch('app.video.render_validator.shutil.which',return_value='/usr/bin/ffprobe')
 @patch('app.video.render_validator.subprocess.run')
 def test_rejects_invalid_duration(self,run,which):
  run.return_value=Mock(returncode=0,stdout=json.dumps({**PROBE,'format':{'duration':'NaN'}}),stderr='')
  with self.assertRaisesRegex(RenderValidationError,'positive duration'): inspect_rendered_video(self.file)
 def test_rejects_missing_file(self):
  with self.assertRaisesRegex(RenderValidationError,'does not exist'): inspect_rendered_video(self.file.parent/'missing.mp4')
if __name__=='__main__': unittest.main()
