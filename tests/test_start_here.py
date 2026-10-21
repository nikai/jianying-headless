"""Portable beginner-flow checks; no editor writes or downloads."""
from copy import deepcopy
import importlib.util
import json
import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('start_here', ROOT / 'tools/start_here.py')
start = importlib.util.module_from_spec(spec)
spec.loader.exec_module(start)


class FirstDraftTests(unittest.TestCase):
    def setUp(self):
        work = ROOT / 'work/onboarding-tests'
        work.mkdir(parents=True, exist_ok=True)
        self.folder = Path(tempfile.mkdtemp(prefix='case-', dir=work))
        self.source = self.folder / "真实 素材's.mp4"
        self.source.write_bytes(b'unit test bytes')
        self.media = {'streams': [{'codec_type': 'video', 'codec_name': 'h264',
            'pix_fmt': 'yuv420p', 'width': 1280, 'height': 720, 'r_frame_rate': '30/1', 'duration': '6.033333'},
            {'codec_type': 'audio', 'codec_name': 'aac'}]}

    def test_drag_paths_and_literal_spaces(self):
        self.assertEqual(start.parse_source(str(self.source)), self.source)
        self.assertEqual(start.parse_source(start.shlex.quote(str(self.source))), self.source)
        escaped = str(self.source).replace(' ', '\\ ').replace("'", "\\'")
        self.assertEqual(start.parse_source(escaped), self.source)

    def test_shell_syntax_is_not_executed(self):
        with self.assertRaises((ValueError, OSError)):
            start.parse_source('$(touch should-not-exist)')
        self.assertFalse((ROOT / 'should-not-exist').exists())

    def test_plan_is_real_media_and_editable_text_without_cache_resources(self):
        plan = start.make_plan(self.source, self.media, 'example')
        self.assertEqual(plan['canvas'], {'width': 1280, 'height': 720, 'fps': 30})
        self.assertEqual([t['type'] for t in plan['tracks']], ['video', 'text'])
        self.assertEqual(plan['tracks'][0]['segments'][0]['source'], str(self.source))
        self.assertTrue(all(t['segments'][0]['duration_us'] == 2000000 for t in plan['tracks']))
        from runtime_profiles import M5_PROFILE, validate_creation_plan
        validate_creation_plan(plan, M5_PROFILE)
        self.assertNotIn('volume', plan['tracks'][0]['segments'][0])

    def test_unsupported_media_is_rejected_not_transcoded(self):
        for change in ({'codec_name': 'hevc'}, {'pix_fmt': 'yuv420p10le'}, {'pix_fmt': 'yuvj420p'},
                       {'width': 1920}, {'height': 1080}, {'r_frame_rate': '25/1'},
                       {'duration': '1.9'}, {'duration': 'NaN'}, {'duration': 'inf'}, {'width': 1079},
                       {'width': 9000}, {'tags': {'rotate': '90'}},
                       {'side_data_list': [{'rotation': -90}]}):
            data = deepcopy(self.media)
            data['streams'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                start.make_plan(self.source, data, 'example')

    def test_audio_must_match_the_verified_aac_input(self):
        for codec in ('mp3', 'pcm_s16le', None):
            data = deepcopy(self.media); data['streams'][1]['codec_name'] = codec
            with self.subTest(codec=codec), self.assertRaisesRegex(ValueError, 'M5 reviewed media'):
                start.make_plan(self.source, data, 'example')
        with self.assertRaisesRegex(ValueError, 'M5 reviewed media'):
            start.make_plan(self.source, {'streams': self.media['streams'][:1]}, 'example')

    def test_multiple_video_streams_rejected(self):
        self.media['streams'].append(deepcopy(self.media['streams'][0]))
        with self.assertRaises(ValueError):
            start.make_plan(self.source, self.media, 'example')

    def test_failed_doctor_does_not_create_output(self):
        def failed(command, timeout=60):
            return subprocess.CompletedProcess(command, 1, '', 'component missing')
        with patch.object(start, 'ROOT', self.folder), patch.object(start, 'run', side_effect=failed):
            with self.assertRaisesRegex(ValueError, 'doctor'):
                start.build(str(self.source))
        self.assertFalse((self.folder / 'work').exists())

    def test_build_never_publishes_or_exports_and_repeat_is_unique(self):
        calls = []
        def success(command, timeout=60):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0,
                json.dumps(self.media) if command[0] == 'ffprobe' else '{}', '')
        with patch.object(start, 'ROOT', self.folder), patch.object(start, 'run', side_effect=success), contextlib.redirect_stdout(io.StringIO()):
            start.build(str(self.source))
            start.build(str(self.source))
        jobs = list((self.folder / 'work').iterdir())
        self.assertEqual(len(jobs), 2)
        self.assertTrue(all('publish' not in c and 'export' not in c and 'create' not in c for c in calls))
        for job in jobs:
            result = json.loads((job / 'next-steps.json').read_text())
            self.assertFalse(result['draft_registered'])
            self.assertFalse(result['video_exported'])
            self.assertEqual(start.shlex.split(result['commands']['publish'])[2], 'publish')
            self.assertEqual(set(result['commands']), {'publish', 'verify'})
            notes = (job / 'next-steps.md').read_text()
            for command in result['commands'].values():
                self.assertIn(command, notes)
            self.assertNotIn(' export ', notes)
        self.assertEqual(self.source.read_bytes(), b'unit test bytes')


if __name__ == '__main__':
    unittest.main()
