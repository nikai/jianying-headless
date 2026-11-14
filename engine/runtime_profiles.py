"""Reviewed application identities; never infer compatibility from a version prefix."""
PRIMARY_VERSION = '11.5.0'
PROFILE_PREFIX = 'jy14-headless-macos-'
# Keys are capability-profile suffixes; the part before '-' is the bundle version.
PROFILES = {
    # Exact M5 identity; capabilities below are scoped to the 2026-10-22 UI trials.
    '11.6.0': '1748fa32a09a967b46515a3acb04863a917b445682d06a64c0e9f0a739db01f1',
    '11.6.0-13281': 'a490d9a08b71a2d9af138d24528d3d40d65b37b06911627c53a2915c6cac0754',
    '11.5.0': '2041482a1aaeffa4d8bd69b836f8cf38807aaad8021bca410d567c59af3bccfa',
    '11.4.2': '632c8ddd09ff4a54f876cd8142eb505055ee26d944199506b230949b7e106bd1',
    '11.4.0': 'a1693070036a6678bb5db35f71d2105812ad24a2370e7e91c78712cc0d6455f3',
}
OFFICIAL_13281_PROFILE = PROFILE_PREFIX + '11.6.0-13281'
EXPORT_PROFILES = frozenset(PROFILE_PREFIX + v for v in ('11.5.0', '11.4.2'))
# Deliverables rendered by the editor's own export dialog. This is a separate
# evidence tier from EXPORT_PROFILES above: it needs no export ABI, proves
# nothing about one, and its acceptance never carries over to that path.
UI_EXPORT_PROFILES = frozenset((PROFILE_PREFIX + '11.6.0',))
# Captured draft resources are reviewed per runtime in the UI, independently of export ABIs.
RESOURCE_PROFILES = frozenset(PROFILE_PREFIX + v for v in ('11.6.0', '11.5.0', '11.4.2'))
EDIT_PROFILES = frozenset(PROFILE_PREFIX + v for v in ('11.6.0', '11.6.0-13281', '11.5.0', '11.4.2', '11.4.0'))
RESOURCE_CAPTURE_PROFILE = PROFILE_PREFIX + '11.4.2'
TIMELINE_SCHEMAS = frozenset((('185.0.0', 360000), ('187.0.0', 360000), ('189.0.0', 360000)))
# Saved formats newer than the builder's 185 are accepted only on runtimes observed reading them:
# 11.5.0 writes 187; the M5 library only demonstrated 185 -> 189.
SCHEMA_RUNTIMES = {'187.0.0': frozenset((PROFILE_PREFIX + '11.5.0',)),
                   '189.0.0': frozenset((PROFILE_PREFIX + '11.6.0', OFFICIAL_13281_PROFILE))}
# Exact native UI save upgrades: runtime -> ({source schemas}, saved schema, stamped app version).
SAVE_UPGRADES = {PROFILE_PREFIX + '11.5.0': (frozenset(('185.0.0',)), '187.0.0', '11.5.0'),
                 PROFILE_PREFIX + '11.6.0': (frozenset(('185.0.0',)), '189.0.0', '11.6.0'),
                 OFFICIAL_13281_PROFILE: (frozenset(('185.0.0',)), '189.0.0', '11.6.0')}


def validate_timeline_schema(timeline, runtime_profile=None):
    schema = (timeline.get('new_version'), timeline.get('version'))
    if type(schema[1]) is not int or schema not in TIMELINE_SCHEMAS:
        raise ValueError('Unexpected native timeline version')
    if runtime_profile is not None:
        known = {PROFILE_PREFIX + version for version in PROFILES}
        readers = SCHEMA_RUNTIMES.get(schema[0])
        if runtime_profile not in known or (readers is not None and runtime_profile not in readers):
            raise ValueError('Native timeline schema is incompatible with this runtime profile')
    return schema


def saved_schema_upgrade(expected, actual, runtime_profile):
    """Recognize only the exact observed UI upgrade; never normalize other fields."""
    before = validate_timeline_schema(expected, runtime_profile)
    after = validate_timeline_schema(actual, runtime_profile)
    if before == after:
        return None
    sources, saved, app_version = SAVE_UPGRADES.get(runtime_profile, ((), None, None))
    if (before[0] in sources and after == (saved, 360000) and before[1] == 360000
            and actual.get('last_modified_platform', {}).get('app_version') == app_version):
        return {'timeline_id': actual['id'], 'before': before[0], 'after': after[0]}
    raise ValueError('Unreviewed native schema migration')


def identity_profile(info, fingerprint):
    """Select one exact library identity before any capability checks."""
    version = info.get('CFBundleShortVersionString')
    if (version not in PROFILES or info.get('CFBundleVersion') != version
            or info.get('CFBundleIdentifier') != 'com.lemon.lvpro'):
        raise ValueError('Unsupported Jianying version/build/identity; stop native writes')
    candidates = {key: sha for key, sha in PROFILES.items() if key.split('-', 1)[0] == version}
    for key, expected in candidates.items():
        if fingerprint == expected:
            return PROFILE_PREFIX + key
    raise ValueError('Editor library differs from its exact headless runtime profile; version='
                     + version + '; actual=' + str(fingerprint) + '; expected='
                     + ','.join(candidates.values())
                     + '. Collect a redacted report with python3 tools/runtime_report.py. '
                     'This build needs review; do not replace the expected hash.')


def validate_identity(info, fingerprint):
    identity_profile(info, fingerprint)
    return info['CFBundleShortVersionString']


def validate_export_profiles(build_profile, runtime_profile):
    if build_profile not in EXPORT_PROFILES or runtime_profile not in EXPORT_PROFILES:
        raise ValueError('No reviewed native export ABI for this build/runtime profile')
    if build_profile != runtime_profile:
        raise ValueError('Build runtime differs from the installed editor; rebuild or edit a copy on the current runtime')


def validate_resource_profile(runtime_profile, capture_profile):
    if capture_profile != RESOURCE_CAPTURE_PROFILE or runtime_profile not in RESOURCE_PROFILES:
        raise ValueError('Native resources need a reviewed runtime profile/capture pairing')


M5_PROFILE = PROFILE_PREFIX + '11.6.0'
# Share the restrictive basic-draft boundary, not the advanced acceptance.
M5_PROFILES = frozenset((M5_PROFILE, OFFICIAL_13281_PROFILE))
M5_COMMANDS = frozenset(('doctor', 'build', 'verify-build', 'publish', 'verify', 'edit', 'ui-export'))


def validate_command(command, runtime_profile):
    if (runtime_profile not in M5_PROFILES or command not in M5_COMMANDS
            or (runtime_profile == OFFICIAL_13281_PROFILE and command == 'ui-export')):
        raise ValueError('M5 supports doctor/build/verify-build/publish/verify, edit and ui-export only; '
                         'official 13281 recovery excludes ui-export')


def validate_creation_plan(plan, runtime_profile, assets=None):
    """Keep basic recovery separate from the advanced M5 creation matrix."""
    if runtime_profile not in M5_PROFILES:
        return
    if plan.get('canvas') not in ({'width': w, 'height': h, 'fps': 30}
                                  for w, h in ((1280, 720), (1920, 1080), (3840, 2160))):
        raise ValueError('M5 canvas requires 720p, 1080p or UHD4K at 30 fps')
    tracks = plan.get('tracks', [])
    if runtime_profile == OFFICIAL_13281_PROFILE:
        for track in tracks:
            if track.get('type') not in {'video', 'text'} or any(
                    set(segment) & {'font_path', 'keyframes', 'mask', 'transition_out'}
                    for segment in track.get('segments', [])):
                raise ValueError('Official 13281 recovery supports basic video/text drafts only')
    if not tracks or tracks[0].get('type') != 'video':
        raise ValueError('M5 requires a main H.264 video track')
    for track in tracks:
        kind = track.get('type')
        if kind not in {'video', 'audio', 'text', 'effect'} or (kind == 'video' and track is not tracks[0]):
            raise ValueError('M5 supports one main video track, text, AAC audio and light-shake tracks')
        allowed = {'source', 'source_start_us', 'source_duration_us', 'start_us', 'duration_us',
                   'volume', 'scale', 'x', 'y', 'rotation', 'opacity', 'keyframes', 'mask', 'transition_out'}
        if kind == 'text':
            allowed = {'text', 'start_us', 'duration_us', 'size', 'x', 'y',
                       'color', 'border_color', 'border_width', 'opacity', 'font_path'}
        elif kind == 'audio':
            allowed = {'source', 'source_start_us', 'source_duration_us', 'start_us', 'duration_us', 'volume'}
        elif kind == 'effect':
            allowed = {'start_us', 'duration_us', 'name', 'params'}
        for segment in track.get('segments', []):
            if set(segment) - allowed:
                raise ValueError('M5 unreviewed segment fields: '
                                 + ', '.join(sorted(set(segment) - allowed)))
            if kind in {'video', 'audio'} and segment.get('source_duration_us', segment.get('duration_us')) != segment.get('duration_us'):
                raise ValueError('M5 supports unit-speed media only')
            if 'font_path' in segment and not str(segment['font_path']).lower().endswith('.ttf'):
                raise ValueError('M5 local fonts require static TTF files')
            if kind == 'effect':
                params = segment.get('params', {})
                if (segment.get('name') != 'light-shake' or not isinstance(params, dict)
                        or any(k not in {'range', 'speed'} or v != {'range': .15, 'speed': .33}[k]
                               for k, v in params.items())):
                    raise ValueError('M5 light-shake supports the captured default parameters only')
            if 'transition_out' in segment:
                transition = segment['transition_out']
                if (not isinstance(transition, dict) or transition.get('name') != 'dissolve'
                        or transition.get('edge_policy', 'require-handles') != 'require-handles'):
                    raise ValueError('M5 transitions require captured dissolve with real source handles')
    if assets is not None:
        for asset in assets:
            if (asset.get('kind') == 'audio' and asset.get('media_type') == 'music'
                    and asset.get('codec') == 'aac' and asset.get('audio_codec') == 'aac'
                    and asset.get('has_audio') is True):
                continue
            if (asset.get('kind') != 'video' or asset.get('media_type') != 'video'
                    or asset.get('codec') != 'h264'):
                raise ValueError('M5 supports H.264 video and independent AAC audio only')
            if (asset.get('pix_fmt') != 'yuv420p' or asset.get('audio_codec') != 'aac'
                    or asset.get('has_audio') is not True or asset.get('r_frame_rate') != '30/1'
                    or (asset.get('width'), asset.get('height')) != (plan['canvas']['width'], plan['canvas']['height'])):
                raise ValueError('M5 reviewed media must match its canvas: H.264/yuv420p at 30 fps with AAC audio')
