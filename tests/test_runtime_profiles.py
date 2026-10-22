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

    def test_m5_capabilities_keep_native_export_closed(self):
        p = profiles.M5_PROFILE
        for allowed in (profiles.RESOURCE_PROFILES, profiles.EDIT_PROFILES, profiles.UI_EXPORT_PROFILES):
            self.assertIn(p, allowed)
        self.assertNotIn(p, profiles.EXPORT_PROFILES)
        profiles.validate_resource_profile(p, profiles.RESOURCE_CAPTURE_PROFILE)
        for command in profiles.M5_COMMANDS:
            profiles.validate_command(command, p)
        for other in ('jy14-headless-macos-11.5.0', 'jy14-headless-macos-11.4.2', None):
            with self.assertRaises(ValueError): profiles.validate_command('doctor', other)
        for command in ('export', 'create', 'resume-publish', 'from-compiled', 'cached-sound'):
            with self.assertRaises(ValueError): profiles.validate_command(command, p)

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
        self.assertIn(runtime,profiles.EDIT_PROFILES)
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
        self.asset = {'kind': 'video', 'media_type': 'video', 'codec': 'h264',
                      'pix_fmt': 'yuv420p', 'audio_codec': 'aac', 'has_audio': True,
                      'r_frame_rate': '30/1', 'width': 1280, 'height': 720, 'duration_us': 4000000}

    def test_plain_video_and_subtitle_are_accepted(self):
        profiles.validate_creation_plan(self.plan, self.profile, [self.asset])

    def bad_plans(self):
        from copy import deepcopy
        for canvas in ({'width': 1920}, {'height': 1080}, {'fps': 24}, {'fps': 25}, {'fps': 50}, {'fps': 60}):
            bad = deepcopy(self.plan); bad['canvas'].update(canvas)
            yield 'canvas/' + str(canvas), bad
        for kind in ('audio', 'filter', 'effect', 'compound'):
            bad = deepcopy(self.plan); bad['tracks'][1]['type'] = kind
            yield kind, bad
        for kind, fields in (('video', {'keyframes': {}, 'mask': {}, 'transition_out': {},
                                      'speed': 1.5}),
                             ('text', {'font_path': '/unused/font.otf', 'text_effect': 'test',
                                       'keyframes': {}})):
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

    def test_main_build_rejects_unreviewed_media_before_output(self):
        from unittest.mock import patch
        for fields in ({'pix_fmt': 'yuvj420p'}, {'pix_fmt': 'yuv420p10le'}, {'pix_fmt': None},
                       {'audio_codec': 'mp3'}, {'audio_codec': 'pcm_s16le'}, {'audio_codec': None},
                       {'has_audio': False}, {'width': 1920}, {'height': 1080}, {'r_frame_rate': '25/1'}):
            with self.subTest(fields=fields), patch.object(self.j.nd, 'doctor', return_value={'runtime_profile': self.profile}), \
                    patch.object(self.j, 'read_json', return_value=self.plan), \
                    patch.object(self.j, 'regular_file', return_value=Path('/unused/source.mp4')), \
                    patch.object(self.j, 'probe', return_value=dict(self.asset, **fields)), \
                    patch.object(self.j.nd, 'fresh_directory') as output:
                with self.assertRaisesRegex(ValueError, 'M5 reviewed media'):
                    self.j.build('unused', 'unused')
                output.assert_not_called()

    def plain_timeline(self):
        target = Path('/unused/Joker-m5-boundary')
        source = self.plan['tracks'][0]['segments'][0]['source']
        asset = dict(self.asset, source=source, sha256='a' * 64, size=10,
                     local_id='media-local-id', relative='Resources/source.mp4')
        timeline, _ = self.j.timeline_for(self.plan, {source: asset}, target, 'timeline-id', self.j.blueprint())
        metadata = {'draft_fold_path': str(target), 'draft_name': target.name,
                    'draft_materials': [{'type': 0, 'value': [self.j.library_record(asset, target, 0)]}]}
        return timeline, metadata, [asset], target

    def test_plain_timeline_passes_structure_before_and_after_save(self):
        from copy import deepcopy
        timeline, metadata, assets, target = self.plain_timeline()
        self.assertTrue(timeline['materials']['speeds'])
        self.assertTrue(timeline['materials']['material_animations'])
        self.assertTrue(timeline['materials']['texts'])
        for schema in ('185.0.0', '189.0.0'):
            for explicit in (True, False):
                actual = deepcopy(timeline); actual['new_version'] = schema
                for track in actual['tracks']:
                    for segment in track['segments']:
                        if explicit:
                            segment['clip']['alpha'] = 1; segment['visible'] = True
                        else:
                            segment['clip'].pop('alpha', None); segment.pop('visible', None)
                with self.subTest(schema=schema, explicit=explicit):
                    self.assertEqual(self.j.verify_structure(actual, metadata, self.plan, assets, target,
                                                            runtime_profile=self.profile), [])

    def test_planned_opacity_and_video_keyframes_are_verified_not_ignored(self):
        from copy import deepcopy
        self.plan['tracks'][0]['segments'][0]['opacity'] = .6
        self.plan['tracks'][0]['segments'][0]['keyframes'] = {'x': [
            {'at_us': 0, 'value': 0}, {'at_us': 4000000, 'value': .25}]}
        timeline, metadata, assets, target = self.plain_timeline()
        self.j.verify_structure(timeline, metadata, self.plan, assets, target, runtime_profile=self.profile)
        for mutation in ('opacity', 'keyframe'):
            bad = deepcopy(timeline); segment = bad['tracks'][0]['segments'][0]
            if mutation == 'opacity': segment['clip']['alpha'] = .7
            else: segment['common_keyframes'][0]['keyframe_list'][1]['values'][0] = .5
            with self.assertRaises(ValueError):
                self.j.verify_structure(bad, metadata, self.plan, assets, target, runtime_profile=self.profile)

    def test_hidden_or_transparent_video_and_text_are_rejected(self):
        from copy import deepcopy
        timeline, metadata, assets, target = self.plain_timeline()
        for ti in (0, 1):
            for field, value in [('alpha', 0), ('alpha', 0.5), ('alpha', True), ('alpha', '1'),
                                 ('alpha', float('nan')), ('visible', False), ('visible', 1), ('visible', None)]:
                actual = deepcopy(timeline); segment = actual['tracks'][ti]['segments'][0]
                (segment['clip'] if field == 'alpha' else segment)[field] = value
                with self.subTest(track=ti, field=field, value=value), self.assertRaisesRegex(ValueError, 'M5 (clip alpha|segment must remain visible)'):
                    self.j.verify_structure(actual, metadata, self.plan, assets, target, runtime_profile=self.profile)

    def test_legacy_record_media_facts_are_bound_to_unchanged_bytes_in_memory(self):
        from unittest.mock import patch
        from copy import deepcopy
        source = self.plan['tracks'][0]['segments'][0]['source']
        actual = dict(self.asset, source=source, sha256='a' * 64)
        recorded = {key: value for key, value in actual.items() if key not in {'pix_fmt', 'audio_codec', 'r_frame_rate'}}
        untouched = deepcopy(recorded)
        with patch.object(self.j, 'validate_plan', return_value=({source: actual}, 4000000, {})):
            enriched = self.j.verified_plan_assets(self.plan, [recorded], self.profile)
            self.assertEqual(enriched[0], actual)
            self.assertEqual(recorded, untouched)
            for bad in (dict(recorded, sha256='b' * 64), dict(recorded, pix_fmt='yuv420p10le')):
                with self.assertRaisesRegex(ValueError, 'Recorded (source media changed|media facts differ)'):
                    self.j.verified_plan_assets(self.plan, [bad], self.profile)

    def test_unreviewed_edit_operations_fail_before_source_access(self):
        from unittest.mock import patch
        import native_edit as edit
        for op in ('create_compound', 'replace_media', 'duplicate_segment', 'remove_segment', 'set_text_font', 'set_filter_intensity'):
            plan = {'schema': edit.SCHEMA, 'name': 'Joker-copy', 'source': {}, 'operations': [{'op': op}]}
            with self.subTest(op=op), patch.object(self.j.nd, 'doctor', return_value={'runtime_profile': self.profile}), \
                    patch.object(self.j, 'read_json', return_value=plan), patch.object(edit, 'load_source') as load:
                with self.assertRaisesRegex(ValueError, 'M5 edits support'): edit.build('unused', 'unused')
                load.assert_not_called()
        for field in ('speed', 'visible', 'opacity', 'scale', 'x', 'y', 'rotation'):
            with self.assertRaisesRegex(ValueError, 'M5 segment edits'):
                edit.validate_m5_operations([{'op': 'set_segment', 'set': {field: 1}}], self.profile)
        edit.validate_m5_operations([{'op': 'replace_text'}, {'op': 'set_segment', 'set': {'volume': .25}}], self.profile)
        edit.validate_m5_operations([{'op': 'create_compound'}], 'jy14-headless-macos-11.5.0')

    def test_verifiers_reject_unreviewed_recorded_plans_before_codec(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        work = ROOT / 'work/m5-scope-fix'
        work.mkdir(parents=True, exist_ok=True)
        for label, plan in self.bad_plans():
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=work) as name:
                folder = Path(name)
                (folder / 'draft').mkdir()
                raw = json.dumps(plan).encode(); (folder / 'plan.json').write_bytes(raw)
                record = {'schema': 'jy14-headless-build/v1', 'blueprint_sha256': self.j.BLUEPRINT_SHA,
                          'runtime_manifest': self.j.nd.MANIFEST_SHA, 'runtime_profile': self.profile,
                          'runtime': {'libvideoeditor_sha256': profiles.PROFILES['11.6.0']},
                          'plan_sha256': self.j.nd.digest(folder / 'plan.json'), 'files': {}, 'assets': [self.asset]}
                (folder / 'build.json').write_text(json.dumps(record))
                with patch.object(self.j.nd, 'doctor', return_value={'runtime_profile': self.profile,
                        'libvideoeditor_sha256': profiles.PROFILES['11.6.0']}), \
                        patch.object(self.j.nd, 'helper') as helper:
                    for operation in (self.j.verify_build, self.j.verify_live):
                        with self.assertRaises(ValueError): operation(folder)
                    helper.assert_not_called()

    def test_readback_rejects_unplanned_native_effects_fonts_and_animation(self):
        from copy import deepcopy
        timeline, metadata, assets, target = self.plain_timeline()
        cases = []
        for bucket in ('audios', 'drafts', 'common_mask', 'video_effects', 'transitions', 'effects'):
            actual = deepcopy(timeline); actual['materials'][bucket] = [{'id': 'unplanned'}]
            cases.append(actual)
        for bucket, field, value in [('material_animations', 'animations', [{}]), ('speeds', 'curve_speed', {})]:
            actual = deepcopy(timeline); actual['materials'][bucket][0][field] = value; cases.append(actual)
        actual = deepcopy(timeline); actual['materials']['canvases'][0]['path'] = '/unplanned/background'; cases.append(actual)
        actual = deepcopy(timeline); actual['tracks'][0]['segments'][0]['clip']['flip'] = {'horizontal': True}; cases.append(actual)
        actual = deepcopy(timeline); actual['materials']['videos'][0]['width'] = 1920; cases.append(actual)
        actual = deepcopy(timeline); actual['materials']['videos'][0]['has_audio'] = False; cases.append(actual)
        actual = deepcopy(timeline); actual['materials']['texts'][0]['font_path'] = '/custom.ttf'; cases.append(actual)
        for field in ('common_keyframes', 'keyframe_refs'):
            actual = deepcopy(timeline); actual['tracks'][0]['segments'][0][field] = [{}]; cases.append(actual)
        for actual in cases:
            with self.assertRaises(ValueError):
                self.j.verify_structure(actual, metadata, self.plan, assets, target, runtime_profile=self.profile)

    def test_new_matrix_and_precise_field_limits(self):
        from copy import deepcopy
        for w, h in ((1280, 720), (1920, 1080), (3840, 2160)):
            plan = deepcopy(self.plan); plan['canvas'].update(width=w, height=h)
            profiles.validate_creation_plan(plan, self.profile, [dict(self.asset, width=w, height=h)])
        plan = deepcopy(self.plan)
        plan['tracks'][0]['segments'][0].update(x=.1, y=-.1, scale=.8, rotation=15, opacity=.6, volume=.5,
            keyframes={k: [{'at_us': 0, 'value': v}, {'at_us': 4000000, 'value': v}] for k,v in
                       [('x', .1), ('y', -.1), ('scale', .8), ('rotation', 15), ('opacity', .6), ('volume', .5)]})
        profiles.validate_creation_plan(plan, self.profile, [self.asset])
        for kind, field, value in [('audio', 'keyframes', {}), ('text', 'keyframes', {}),
                                  ('text', 'font_path', '/unused/font.otf')]:
            bad = deepcopy(self.plan); bad['tracks'][1]['type'] = kind; bad['tracks'][1]['segments'][0][field] = value
            with self.assertRaises(ValueError): profiles.validate_creation_plan(bad, self.profile)
        for params in ({'range': .2}, {'speed': .5}, {'other': .15}, None):
            bad = deepcopy(self.plan); bad['tracks'].append({'type': 'effect', 'segments': [{'name': 'light-shake', 'params': params}]})
            with self.assertRaises(ValueError): profiles.validate_creation_plan(bad, self.profile)
        profiles.validate_creation_plan(self.plan, self.profile, [self.asset, {'kind': 'audio', 'media_type': 'music',
            'codec': 'aac', 'audio_codec': 'aac', 'has_audio': True}])

    def test_edit_rejects_complex_and_old_schema_sources(self):
        from unittest.mock import patch
        from copy import deepcopy
        import native_edit as edit
        timeline, _, assets, target = self.plain_timeline()
        with patch.object(self.j, 'probe', return_value=assets[0]):
            edit.validate_m5_source(timeline, target, self.profile)
            for bucket in ('drafts', 'common_mask', 'video_effects'):
                bad = deepcopy(timeline); bad['materials'][bucket] = [{'id': 'complex'}]
                with self.assertRaises(ValueError): edit.validate_m5_source(bad, target, self.profile)
            bad = deepcopy(timeline); bad['new_version'] = '187.0.0'
            with self.assertRaises(ValueError): edit.validate_m5_source(bad, target, self.profile)

    def test_m5_rejects_parsed_otf_even_when_named_ttf(self):
        from copy import deepcopy
        from unittest.mock import patch
        plan = deepcopy(self.plan)
        path = '/unused/renamed.ttf'
        plan['tracks'][1]['segments'][0]['font_path'] = path
        asset = {'source': path, 'format': 'otf'}
        with patch.object(self.j, 'regular_file', return_value=Path('/unused/source.mp4')), \
                patch.object(self.j, 'probe', return_value=self.asset), \
                patch.object(self.j.fonts, 'asset_for', return_value=asset), \
                patch.object(self.j.fonts, 'verify_glyphs') as glyphs:
            with self.assertRaisesRegex(ValueError, 'parsed static TTF'):
                self.j.validate_plan(plan, self.profile)
            glyphs.assert_not_called()
        timeline, metadata, assets, target = self.plain_timeline()
        with self.assertRaisesRegex(ValueError, 'parsed static TTF'):
            self.j.verify_structure(timeline, metadata, self.plan, assets, target,
                                    runtime_profile=self.profile, font_assets=[asset])

    def test_explicit_static_font_requires_glyph_coverage(self):
        import importlib.util
        import native_fonts
        font = Path('/System/Library/Fonts/Monaco.ttf')
        if not font.is_file() or importlib.util.find_spec('fontTools') is None:
            self.skipTest('Local font coverage requires the optional pinned fontTools and Monaco')
        native_fonts.verify_glyphs(font, 'Joker 123')
        with self.assertRaisesRegex(ValueError, 'missing glyphs'):
            native_fonts.verify_glyphs(font, '\U0010ffff')



class BuildRuntimeProvenance(unittest.TestCase):
    def setUp(self):
        import tempfile
        import jy14_headless as j
        self.j = j
        work = ROOT / 'work/m5-review-r1-fix'
        work.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=work)
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.runtime = {'runtime_profile': profiles.M5_PROFILE,
                        'libvideoeditor_sha256': profiles.PROFILES['11.6.0']}
        self.record = {'runtime_profile': profiles.M5_PROFILE, 'runtime': dict(self.runtime)}

    def test_matching_library_is_accepted_but_matching_profile_alone_is_not(self):
        self.j.validate_build_runtime(self.record, self.runtime)
        with self.assertRaisesRegex(ValueError, 'Build runtime differs'):
            self.j.validate_build_runtime(dict(self.record, runtime_profile='other'), self.runtime)

    def test_old_missing_and_unknown_library_are_rejected_by_all_three_operations(self):
        from copy import deepcopy
        from unittest.mock import patch
        variants = [
            {'libvideoeditor_sha256': 'a490d9a08b71a2d9af138d24528d3d40d65b37b06911627c53a2915c6cac0754'},
            {'libvideoeditor_sha256': '0' * 64}, {}, None,
        ]
        for captured in variants:
            record = deepcopy(self.record); record['runtime'] = captured
            (self.folder / 'build.json').write_text(json.dumps(record))
            with self.subTest(captured=captured), patch.object(self.j.nd, 'doctor', return_value=self.runtime), \
                    patch.object(self.j.nd, 'helper') as helper:
                operations = [lambda: self.j.verify_build(self.folder),
                              lambda: self.j.verify_live(self.folder),
                              lambda: self.j.publish(self.folder, self.folder / 'audit')]
                for operation in operations:
                    with self.assertRaisesRegex(ValueError, 'Build editor library differs'):
                        operation()
                helper.assert_not_called()
                self.assertFalse((self.folder / 'audit').exists())

    def test_publish_rechecks_library_after_the_build_verifier(self):
        from unittest.mock import Mock, patch
        # Even an injected verifier cannot skip the fresh signed-runtime check.
        helper = Mock()
        helper._validate_runtime_environment.return_value = dict(self.runtime, libvideoeditor_sha256='f' * 64)
        with patch.object(self.j.nd, 'helper', return_value=helper):
            with self.assertRaisesRegex(ValueError, 'Build editor library differs'):
                self.j.publish(self.folder, self.folder / 'audit', verify_build_fn=lambda _: self.record)
        helper._ensure_editor_closed.assert_not_called()
        helper._acquire_directory_transaction_lock.assert_not_called()
        self.assertFalse((self.folder / 'audit').exists())


if __name__=='__main__':
    unittest.main()
