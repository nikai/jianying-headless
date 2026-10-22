"""Offline checks for the UI export acceptance path.

The editor does the rendering, so these tests cover the part that is ours: which
containers this path accepts, that it inherits the exact frame-count policy
instead of relaxing it, which runtimes it is registered for, and the draft-change
report. No app, codec, media, draft or network is needed.

Passing here establishes nothing about a real export; the 2026-10-20 acceptance
is recorded in docs/VERIFICATION.md.
"""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'engine'))
import runtime_profiles as profiles  # noqa: E402
import ui_export  # noqa: E402

SETTINGS = {'width': 640, 'height': 360, 'fps': 30, 'bitrate': 4_000_000, 'timeout_seconds': 600}


def probe(frames, brand='qt  ', duration='2.000000', audio=True, **video):
    streams = [dict({'codec_type': 'video', 'codec_name': 'h264', 'width': 640, 'height': 360,
                     'r_frame_rate': '30/1', 'nb_frames': str(frames)}, **video)]
    if audio:
        streams.append({'codec_type': 'audio', 'codec_name': 'aac'})
    return {'streams': streams, 'format': {'duration': duration, 'tags': {'major_brand': brand}}}


class ContainerTests(unittest.TestCase):
    def test_the_editors_quicktime_branded_mov_is_accepted_and_reported(self):
        media = ui_export.validate_container(probe(60), SETTINGS, 2_000_000, True)
        self.assertEqual(media['major_brand'], 'qt  ')
        self.assertEqual(media['container_writer'], 'Jianying export dialog')
        self.assertEqual((media['frames'], media['expected_frames']), (60, 60))

    def test_every_reviewed_brand_is_accepted_and_others_are_not(self):
        for brand in ui_export.CONTAINER_BRANDS:
            with self.subTest(brand=brand):
                self.assertEqual(
                    ui_export.validate_container(probe(60, brand), SETTINGS, 2_000_000, True)['major_brand'],
                    brand)
        for brand in ('avi', 'matroska', '', None, 'QT  '):
            with self.subTest(rejected=brand), self.assertRaises(ValueError):
                ui_export.validate_container(probe(60, brand), SETTINGS, 2_000_000, True)

    def test_the_headless_brand_set_is_not_widened_by_this_path(self):
        import native_export
        self.assertNotIn('qt  ', ('isom', 'mp41', 'mp42'))
        with self.assertRaises(ValueError):
            native_export.validate_probe(probe(60), SETTINGS, 2_000_000, True)

    def test_a_short_or_long_export_is_still_refused(self):
        for frames in (59, 61, 0):
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                ui_export.validate_container(probe(frames), SETTINGS, 2_000_000, True)

    def test_canvas_rate_codec_and_missing_audio_stay_strict(self):
        cases = {
            'canvas': dict(width=1280),
            'rate': dict(r_frame_rate='25/1'),
            'codec': dict(codec_name='hevc'),
        }
        for name, override in cases.items():
            with self.subTest(case=name), self.assertRaises(ValueError):
                ui_export.validate_container(probe(60, **override), SETTINGS, 2_000_000, True)
        with self.assertRaises(ValueError):
            ui_export.validate_container(probe(60, audio=False), SETTINGS, 2_000_000, True)

    def test_the_input_probe_is_not_mutated_by_the_brand_substitution(self):
        info = probe(60)
        before = deepcopy(info)
        ui_export.validate_container(info, SETTINGS, 2_000_000, True)
        self.assertEqual(info, before)


class ProfileTests(unittest.TestCase):
    def test_only_the_verified_m5_ui_export_profile_is_enabled(self):
        self.assertEqual(profiles.UI_EXPORT_PROFILES,
                         frozenset((profiles.M5_PROFILE,)))

    def test_this_set_is_separate_from_the_headless_export_set(self):
        self.assertFalse(profiles.UI_EXPORT_PROFILES & profiles.EXPORT_PROFILES)
        self.assertEqual(profiles.EXPORT_PROFILES,
                         frozenset(profiles.PROFILE_PREFIX + v for v in ('11.5.0', '11.4.2')))


class PlanFormatTests(unittest.TestCase):
    def test_verify_keeps_decode_frame_and_draft_checks_on_the_formal_path(self):
        import jy14_headless as j
        import subprocess
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary); build = folder / 'build'; build.mkdir()
            (build / 'build.json').write_text('{}')
            target = folder / 'draft'; target.mkdir()
            job = folder / 'job'; job.mkdir()
            output = folder / 'synthetic.mov'; output.write_bytes(b'synthetic encoded bytes')
            runtime = {'runtime_profile': profiles.M5_PROFILE, 'libvideoeditor_sha256': profiles.PROFILES['11.6.0']}
            document = {'schema': ui_export.PLAN_SCHEMA, 'ui_used': True, 'build': str(build),
                'build_sha256': j.nd.digest(build / 'build.json'), 'draft': str(target), 'draft_name': target.name,
                'runtime': runtime, 'settings': SETTINGS, 'duration_us': 2000000, 'audio_expected': True,
                'expected_output': str(output), 'readback_before_export': {'status': 'verified'}}
            j.write(job / 'plan.json', document)
            timeline = {'duration': 2000000, 'tracks': [], 'materials': {}}
            with patch.object(ui_export, 'live_record', return_value=(build, {'target': str(target)}, {'status': 'verified'})) as live, \
                    patch.object(ui_export, 'expectations', return_value=(timeline, runtime, SETTINGS, True)), \
                    patch.object(ui_export, 'probe', return_value=probe(60)), \
                    patch.object(ui_export.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'', b'')) as decode:
                result = ui_export.verify(job)
            live.assert_called_once_with(build)
            self.assertEqual(result['media']['frames'], 60)
            self.assertTrue(result['full_decode_passed'])
            self.assertIn('-xerror', decode.call_args.args[0])
            self.assertEqual(result['renderer'], 'Jianying export dialog')
            self.assertTrue((job / 'attempt-001/result.json').is_file())

    def test_changed_frozen_build_is_rejected_before_live_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            with patch.object(ui_export.j, 'read_json', return_value={'schema': 'jy14-headless-build/v1'}), \
                    patch.object(ui_export.j, 'verify_build', side_effect=ValueError('snapshot changed')), \
                    patch.object(ui_export.j, 'verify_live') as live:
                with self.assertRaisesRegex(ValueError, 'snapshot changed'):
                    ui_export.live_record(folder)
                live.assert_not_called()

    def test_verify_rejects_a_plan_bound_to_another_draft(self):
        import jy14_headless as j
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary); build = folder / 'build'; build.mkdir()
            (build / 'build.json').write_text('{}')
            job = folder / 'job'; job.mkdir()
            j.write(job / 'plan.json', {'schema': ui_export.PLAN_SCHEMA, 'ui_used': True,
                'build': str(build), 'build_sha256': j.nd.digest(build / 'build.json'),
                'draft': str(folder / 'other-draft'), 'draft_name': 'other-draft'})
            with patch.object(ui_export, 'live_record', return_value=(build, {'target': str(folder / 'actual-draft')}, {})), \
                    patch.object(ui_export, 'expectations') as expectations:
                with self.assertRaisesRegex(ValueError, 'draft binding changed'):
                    ui_export.verify(job)
                expectations.assert_not_called()

    def test_plan_requests_the_mov_format_actually_exported_by_the_editor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build = root / 'build'; build.mkdir()
            (build / 'build.json').write_text('{}')
            target = root / 'draft'; target.mkdir()
            record = {'target': str(target)}
            report = {'status': 'verified'}
            timeline = {'duration': 4_000_000}
            job = root / 'work' / 'export'
            with patch.object(ui_export, 'live_record', return_value=(build, record, report)), \
                    patch.object(ui_export, 'expectations', return_value=(timeline, {}, SETTINGS, True)):
                document = ui_export.plan(build, job)
            self.assertEqual(document['dialog_settings_required']['格式'], 'MOV')
            self.assertTrue(document['expected_output'].endswith('/draft.mov'))
            self.assertTrue(document['ui_used'])


class DraftChangeTests(unittest.TestCase):
    def manifest(self, folder, files):
        for name, body in files.items():
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding='utf-8')

    def test_what_the_editor_touched_is_counted_and_named(self):
        import jy14_headless as j
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'draft'
            folder.mkdir()
            self.manifest(folder, {'draft_info.json': 'one', 'gone.txt': 'two'})
            document = {'draft_files_before': j.files_manifest(folder)}
            (folder / 'gone.txt').unlink()
            (folder / 'draft_info.json').write_text('changed', encoding='utf-8')
            self.manifest(folder, {'.backup/new.bak': 'three'})
            changes = ui_export.draft_changes(document, folder)
        self.assertEqual((changes['added'], changes['changed'], changes['removed']), (1, 1, 1))
        self.assertEqual(changes['changed_names'], ['draft_info.json'])
        self.assertEqual(changes['removed_names'], ['gone.txt'])
        self.assertIn('source-unchanged', changes['note'])

    def test_an_untouched_draft_reports_nothing(self):
        import jy14_headless as j
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'draft'
            folder.mkdir()
            self.manifest(folder, {'draft_info.json': 'one'})
            changes = ui_export.draft_changes({'draft_files_before': j.files_manifest(folder)}, folder)
        self.assertEqual((changes['added'], changes['changed'], changes['removed']), (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
