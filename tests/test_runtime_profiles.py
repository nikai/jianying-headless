"""Version selection and fail-closed guards, without changing the installed app."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'engine'))
import runtime_profiles as profiles


class RuntimeProfiles(unittest.TestCase):
    def info(self, version):
        return {'CFBundleShortVersionString': version, 'CFBundleVersion': version,
                'CFBundleIdentifier': 'com.lemon.lvpro'}

    def test_primary_and_legacy_identities(self):
        self.assertEqual(profiles.PRIMARY_VERSION, '11.5.0')
        for v,h in profiles.PROFILES.items():
            self.assertEqual(profiles.validate_identity(self.info(v),h),v)

    def test_exact_1142_fingerprint_is_preserved(self):
        self.assertEqual(profiles.PROFILES['11.4.2'],
                         '632c8ddd09ff4a54f876cd8142eb505055ee26d944199506b230949b7e106bd1')

    def test_exact_1160_fingerprint_matches_m5_experimental_package(self):
        self.assertEqual(profiles.PROFILES['11.6.0'],
                         '1748fa32a09a967b46515a3acb04863a917b445682d06a64c0e9f0a739db01f1')

    def test_m5_has_only_plain_creation_capabilities(self):
        p=profiles.PROFILE_PREFIX+'11.6.0'
        for allowed in (profiles.RESOURCE_PROFILES, profiles.EDIT_PROFILES,
                        profiles.EXPORT_PROFILES, profiles.UI_EXPORT_PROFILES):
            self.assertNotIn(p, allowed)
        with self.assertRaises(ValueError):
            profiles.validate_resource_profile(p,profiles.RESOURCE_CAPTURE_PROFILE)
        for command in profiles.M5_COMMANDS:
            profiles.validate_command(command,p)
        for other in ('jy14-headless-macos-11.5.0', 'jy14-headless-macos-11.4.2', None):
            with self.subTest(runtime=other), self.assertRaises(ValueError):
                profiles.validate_command('doctor',other)
        for command in ('edit', 'export', 'ui-export', 'create', 'resume-publish', 'from-compiled', 'cached-sound'):
            with self.subTest(command=command), self.assertRaises(ValueError):
                profiles.validate_command(command,p)

    def test_mismatched_hash_build_bundle_and_unknown_version_rejected(self):
        for version in ('11.6.0','11.5.0','11.4.2'):
            h=profiles.PROFILES[version]
            bad=[(self.info(version),'0'*64)]
            for key,val in [('CFBundleVersion','unexpected'),('CFBundleIdentifier','com.other')]:
                info=self.info(version);info[key]=val;bad.append((info,h))
            for info,sha in bad:
                with self.subTest(version=version,info=info),self.assertRaises(ValueError):
                    profiles.validate_identity(info,sha)
        with self.assertRaises(ValueError):
            profiles.validate_identity(self.info('11.5.1'),profiles.PROFILES['11.5.0'])

    def test_export_only_allows_same_reviewed_runtime(self):
        for v in ('11.5.0','11.4.2'):
            p=profiles.PROFILE_PREFIX+v
            profiles.validate_export_profiles(p,p)
        for a,b in [('11.4.2','11.5.0'),('11.5.0','11.4.2'),('11.4.0','11.4.0'),('11.5.1','11.5.1'),
                    ('11.6.0','11.6.0'),('11.5.0','11.6.0'),('11.6.0','11.5.0')]:
            with self.subTest(a=a,b=b),self.assertRaises(ValueError):
                profiles.validate_export_profiles(profiles.PROFILE_PREFIX+a,profiles.PROFILE_PREFIX+b)

    def test_resource_pairing_keeps_capture_provenance(self):
        for p in profiles.RESOURCE_PROFILES:
            profiles.validate_resource_profile(p,profiles.RESOURCE_CAPTURE_PROFILE)
        with self.assertRaises(ValueError):
            profiles.validate_resource_profile(profiles.PROFILE_PREFIX+'11.4.0',profiles.RESOURCE_CAPTURE_PROFILE)
        with self.assertRaises(ValueError):
            profiles.validate_resource_profile(profiles.PROFILE_PREFIX+'11.5.0',profiles.PROFILE_PREFIX+'11.5.0')

    def test_timeline_schema_is_version_scoped(self):
        old = {'new_version':'185.0.0','version':360000}
        new = {'new_version':'187.0.0','version':360000}
        newest = {'new_version':'189.0.0','version':360000}
        for version in ('11.4.0','11.4.2','11.5.0','11.6.0'):
            profiles.validate_timeline_schema(old,profiles.PROFILE_PREFIX+version)
        for version in ('11.5.0',):
            profiles.validate_timeline_schema(new,profiles.PROFILE_PREFIX+version)
        profiles.validate_timeline_schema(newest,profiles.PROFILE_PREFIX+'11.6.0')
        for version in ('11.4.0','11.4.2','11.5.1','11.6.0','11.6.1'):
            with self.subTest(schema='187',version=version),self.assertRaises(ValueError):
                profiles.validate_timeline_schema(new,profiles.PROFILE_PREFIX+version)
        for version in ('11.4.0','11.4.2','11.5.0','11.6.1'):
            with self.subTest(schema='189',version=version),self.assertRaises(ValueError):
                profiles.validate_timeline_schema(newest,profiles.PROFILE_PREFIX+version)
        for bad in [dict(new,new_version='188.0.0'),dict(new,version=360001),dict(new,version=360000.0),
                    dict(newest,new_version='190.0.0'),dict(newest,version=360001)]:
            with self.assertRaises(ValueError): profiles.validate_timeline_schema(bad)

    def test_ui_upgrade_is_reported_without_mutating_evidence(self):
        old={'id':'sample','new_version':'185.0.0','version':360000}
        new=dict(old,new_version='187.0.0',last_modified_platform={'app_version':'11.5.0'})
        runtime=profiles.PROFILE_PREFIX+'11.5.0'
        change=profiles.saved_schema_upgrade(old,new,runtime)
        self.assertEqual(change,{'timeline_id':'sample','before':'185.0.0','after':'187.0.0'})
        self.assertEqual(new['new_version'],'187.0.0')
        self.assertIsNone(profiles.saved_schema_upgrade(new,new,runtime))
        with self.assertRaises(ValueError): profiles.saved_schema_upgrade(new,old,runtime)
        with self.assertRaises(ValueError):
            profiles.saved_schema_upgrade(old,dict(new,last_modified_platform={}),runtime)

    def test_1160_ui_upgrades_are_exact(self):
        runtime=profiles.PROFILE_PREFIX+'11.6.0'
        saved={'id':'sample','new_version':'189.0.0','version':360000,'last_modified_platform':{'app_version':'11.6.0'}}
        for source in ('185.0.0',):
            before={'id':'sample','new_version':source,'version':360000}
            self.assertEqual(profiles.saved_schema_upgrade(before,saved,runtime),
                             {'timeline_id':'sample','before':source,'after':'189.0.0'})
        self.assertIsNone(profiles.saved_schema_upgrade(saved,saved,runtime))
        old={'id':'sample','new_version':'185.0.0','version':360000}
        bad=[(old,dict(saved,last_modified_platform={'app_version':'11.5.0'})),
             (old,dict(saved,new_version='187.0.0',last_modified_platform={'app_version':'11.6.0'})),
             (saved,dict(old,last_modified_platform={'app_version':'11.6.0'}))]
        for before,after in bad:
            with self.subTest(before=before['new_version'],after=after['new_version']),self.assertRaises(ValueError):
                profiles.saved_schema_upgrade(before,after,runtime)
        with self.assertRaises(ValueError):
            profiles.saved_schema_upgrade(old,saved,profiles.PROFILE_PREFIX+'11.5.0')
        self.assertNotIn(runtime,profiles.EDIT_PROFILES)
        with self.assertRaises(ValueError):
            profiles.saved_schema_upgrade(dict(old,new_version="187.0.0"),saved,runtime)


class M5CreationBoundary(unittest.TestCase):
    """Exercise runtime gates before build writes or codec/resource access."""
    def setUp(self):
        import jy14_headless as j
        self.j = j
        self.profile = profiles.M5_PROFILE
        self.plan = {'schema': j.SCHEMA, 'name': 'Joker-m5-boundary',
                     'canvas': {'width': 1280, 'height': 720, 'fps': 30},
                     'tracks': [{'type': 'video', 'segments': [
                         {'source': '/unused/source.mp4', 'duration_us': 4000000}]},
                         {'type': 'text', 'segments': [{'text': '字幕', 'duration_us': 4000000}]}]}
        self.asset = {'kind': 'video', 'media_type': 'video', 'codec': 'h264'}

    def test_plain_video_and_subtitle_are_accepted(self):
        profiles.validate_creation_plan(self.plan, self.profile, [self.asset])

    def bad_plans(self):
        from copy import deepcopy
        for kind in ('audio', 'filter', 'effect', 'compound'):
            bad = deepcopy(self.plan); bad['tracks'][1]['type'] = kind
            yield kind, bad
        for kind, fields in (('video', {'keyframes': {}, 'mask': {}, 'transition_out': {},
                                      'speed': 1.5, 'volume': 0.5, 'scale': 2, 'opacity': 0.5}),
                             ('text', {'font_path': '/unused/font.ttf', 'text_effect': 'test',
                                       'keyframes': {}, 'opacity': 0.5})):
            for field, value in fields.items():
                bad = deepcopy(self.plan)
                bad['tracks'][0 if kind == 'video' else 1]['segments'][0][field] = value
                yield kind + '/' + field, bad
        bad = deepcopy(self.plan)
        bad['tracks'][0]['segments'][0]['source_duration_us'] = 5000000
        yield 'nonunit-speed', bad
        bad = deepcopy(self.plan); bad['tracks'].append(deepcopy(bad['tracks'][0]))
        yield 'overlay-video', bad

    def test_unreviewed_plans_fail_before_build_output(self):
        from unittest.mock import patch
        for label, bad in self.bad_plans():
            with self.subTest(label=label), patch.object(self.j.nd, 'doctor', return_value={'runtime_profile': self.profile}), \
                    patch.object(self.j, 'read_json', return_value=bad), \
                    patch.object(self.j.nd, 'fresh_directory') as output, \
                    patch.object(self.j, 'probe') as probe:
                with self.assertRaises(ValueError):
                    self.j.build('unused', 'unused')
                output.assert_not_called(); probe.assert_not_called()

    def test_audio_photos_gif_and_hevc_are_rejected(self):
        for fields in ({'kind': 'audio'}, {'media_type': 'photo', 'codec': 'png'},
                       {'media_type': 'photo', 'codec': 'mjpeg'}, {'media_type': 'gif', 'codec': 'gif'},
                       {'codec': 'hevc'}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                profiles.validate_creation_plan(self.plan, self.profile, [dict(self.asset, **fields)])

    def test_edit_inspection_and_both_verifiers_refuse_before_draft_access(self):
        from unittest.mock import patch
        import native_edit as edit
        with patch.object(self.j.nd, 'doctor', return_value={'runtime_profile': self.profile}), \
                patch.object(self.j.nd, 'helper') as helper:
            for operation in (edit.load_source, edit.verify_build, edit.verify_live):
                with self.subTest(operation=operation.__name__), self.assertRaisesRegex(ValueError, 'profile'):
                    operation('/does-not-exist')
            helper.assert_not_called()

    def test_verifiers_reject_unreviewed_recorded_plans_before_codec(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        work = ROOT / 'work/m5-scope-fix'
        work.mkdir(exist_ok=True)
        for label, plan in self.bad_plans():
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=work) as name:
                folder = Path(name)
                (folder / 'draft').mkdir()
                raw = json.dumps(plan).encode(); (folder / 'plan.json').write_bytes(raw)
                record = {'schema': 'jy14-headless-build/v1', 'blueprint_sha256': self.j.BLUEPRINT_SHA,
                          'runtime_manifest': self.j.nd.MANIFEST_SHA, 'runtime_profile': self.profile,
                          'plan_sha256': self.j.nd.digest(folder / 'plan.json'), 'files': {}, 'assets': [self.asset]}
                (folder / 'build.json').write_text(json.dumps(record))
                with patch.object(self.j.nd, 'doctor', return_value={'runtime_profile': self.profile}), \
                        patch.object(self.j.nd, 'helper') as helper:
                    for operation in (self.j.verify_build, self.j.verify_live):
                        with self.assertRaises(ValueError): operation(folder)
                    helper.assert_not_called()

    def test_readback_rejects_unplanned_native_effects_fonts_and_animation(self):
        from copy import deepcopy
        timeline = {'new_version': '189.0.0', 'version': 360000, 'materials': {}, 'tracks': []}
        cases = [
            ('audios', [{'id': 'audio'}], 'unreviewed native materials'),
            ('drafts', [{'id': 'compound'}], 'unreviewed native materials'),
            ('common_mask', [{'id': 'mask'}], 'unreviewed native materials'),
            ('video_effects', [{'id': 'effect'}], 'unreviewed native materials'),
            ('material_animations', [{'id': 'animation', 'type': 'sticker_animation', 'animations': [{}]}], 'text animation'),
            ('speeds', [{'id': 'speed', 'curve_speed': {}}], 'speed changes'),
            ('texts', [{'font_path': '/custom.ttf'}], 'custom fonts'),
            ('texts', [{'font_path': '/Applications/VideoFusion-macOS.app/Contents/Resources/Font/SystemFont/zh-hans.ttf',
                        'content': json.dumps({'styles': [{'font': {'id': '', 'path': '/custom.ttf'}}]})}], 'custom fonts'),
        ]
        for bucket, nodes, message in cases:
            actual = deepcopy(timeline); actual['materials'][bucket] = nodes
            with self.subTest(bucket=bucket), self.assertRaisesRegex(ValueError, 'M5 ' + message):
                self.j.verify_structure(actual, {}, self.plan, [self.asset], Path('/unused'),
                                        runtime_profile=self.profile)
        for field in ('common_keyframes', 'keyframe_refs'):
            actual = deepcopy(timeline); actual['tracks'] = [{'segments': [{field: [{}]}]}]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'M5 keyframes'):
                self.j.verify_structure(actual, {}, self.plan, [self.asset], Path('/unused'),
                                        runtime_profile=self.profile)


if __name__=='__main__':
    unittest.main()
