import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from app.video.ffmpeg_assembler import VideoAssemblyError, assemble_video
class FfmpegAssemblerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.video=self.root/'in.mp4'; self.audio=self.root/'voice.wav'; self.subs=self.root/'captions.srt'; self.output=self.root/'out.mp4'
        self.video.write_text('fixture',encoding='utf-8'); self.audio.write_text('fixture',encoding='utf-8'); self.subs.write_text('1\n00:00:00,000 --> 00:00:01,000\nValid test subtitle.\n',encoding='utf-8')
    def tearDown(self): self.temp.cleanup()
    @patch('app.video.ffmpeg_assembler.shutil.which',return_value='/usr/bin/ffmpeg')
    @patch('app.video.ffmpeg_assembler.subprocess.run')
    def test_builds_argument_list_without_shell(self,run,which):
        run.return_value=Mock(returncode=0,stderr='')
        def create_output(command,**kwargs): Path(command[-1]).write_bytes(b'fake-video'); return Mock(returncode=0,stderr='')
        run.side_effect=create_output
        result=assemble_video(self.video,self.audio,self.output,self.subs)
        self.assertEqual(result,self.output.resolve())
        args,kwargs=run.call_args
        self.assertIsInstance(args[0],list); self.assertFalse(kwargs.get('shell',False))
        self.assertIn('mov_text',args[0]); self.assertIn('-nostdin',args[0])
    @patch('app.video.ffmpeg_assembler.shutil.which',return_value='/usr/bin/ffmpeg')
    @patch('app.video.ffmpeg_assembler.subprocess.run')
    def test_rejects_invalid_srt_before_running_ffmpeg(self,run,which):
        self.subs.write_text('not a valid subtitle file',encoding='utf-8')
        with self.assertRaisesRegex(VideoAssemblyError,'Subtitle validation failed'):
            assemble_video(self.video,self.audio,self.output,self.subs)
        run.assert_not_called()
    @patch('app.video.ffmpeg_assembler.shutil.which',return_value=None)
    def test_requires_ffmpeg(self,which):
        with self.assertRaisesRegex(VideoAssemblyError,'not found'):
            assemble_video(self.video,self.audio,self.output)
    def test_rejects_missing_input(self):
        with self.assertRaisesRegex(VideoAssemblyError,'does not exist'):
            assemble_video(self.root/'missing.mp4',self.audio,self.output)
    @patch('app.video.ffmpeg_assembler.shutil.which',return_value='/usr/bin/ffmpeg')
    def test_refuses_overwrite_by_default(self,which):
        self.output.write_bytes(b'existing')
        with self.assertRaisesRegex(VideoAssemblyError,'already exists'):
            assemble_video(self.video,self.audio,self.output)
    @patch('app.video.ffmpeg_assembler.shutil.which',return_value='/usr/bin/ffmpeg')
    @patch('app.video.ffmpeg_assembler.subprocess.run')
    def test_reports_ffmpeg_failure(self,run,which):
        run.return_value=Mock(returncode=1,stderr='fixture failure')
        with self.assertRaisesRegex(VideoAssemblyError,'fixture failure'):
            assemble_video(self.video,self.audio,self.output)
    @patch('app.video.ffmpeg_assembler.shutil.which',return_value='/usr/bin/ffmpeg')
    @patch('app.video.ffmpeg_assembler.subprocess.run')
    def test_failed_overwrite_preserves_existing_output(self,run,which):
        self.output.write_bytes(b'original-output')
        run.return_value=Mock(returncode=1,stderr='fixture failure')
        with self.assertRaisesRegex(VideoAssemblyError,'fixture failure'):
            assemble_video(self.video,self.audio,self.output,overwrite=True)
        self.assertEqual(self.output.read_bytes(),b'original-output')
        self.assertEqual(list(self.root.glob('.out.*.mp4')),[])
    @patch('app.video.ffmpeg_assembler.shutil.which',return_value='/usr/bin/ffmpeg')
    @patch('app.video.ffmpeg_assembler.subprocess.run')
    def test_timeout_preserves_existing_output_and_cleans_temp(self,run,which):
        from subprocess import TimeoutExpired
        self.output.write_bytes(b'original-output')
        run.side_effect=TimeoutExpired(cmd='ffmpeg',timeout=1)
        with self.assertRaisesRegex(VideoAssemblyError,'timed out'):
            assemble_video(self.video,self.audio,self.output,overwrite=True,timeout_seconds=1)
        self.assertEqual(self.output.read_bytes(),b'original-output')
        self.assertEqual(list(self.root.glob('.out.*.mp4')),[])
    def test_requires_mp4_output_extension(self):
        with self.assertRaisesRegex(VideoAssemblyError,r'\.mp4 extension'):
            assemble_video(self.video,self.audio,self.root/'out.mkv')
    def test_output_must_differ_from_input(self):
        with self.assertRaisesRegex(VideoAssemblyError,'differ'):
            assemble_video(self.video,self.audio,self.video)
if __name__=='__main__': unittest.main()
