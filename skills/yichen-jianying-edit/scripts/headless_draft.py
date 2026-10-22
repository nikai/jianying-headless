#!/usr/bin/env python3
"""Pinned Skill entrypoint for a separately checked-out Jianying Headless project."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

def project_root():
    configured = os.environ.get('JIANYING_HEADLESS_ROOT')
    if configured:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            raise SystemExit('JIANYING_HEADLESS_ROOT must be an absolute checkout path')
        candidates = [path.resolve()]
    else:
        candidates = list(Path(__file__).resolve().parents) + [Path.home() / 'repos/third-party/jianying-headless']
    for path in candidates:
        marker = path / 'project.json'
        if marker.is_file() and not marker.is_symlink():
            try:
                identity = json.loads(marker.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            if identity.get('id') == 'jianying-headless' and identity.get('schema') == 'jianying-headless-project/v1':
                return path
    raise SystemExit('Jianying Headless checkout unavailable. Clone the project with authorized GitHub access, '
                     'at ~/repos/third-party/jianying-headless, or set JIANYING_HEADLESS_ROOT to an absolute path. '
                     'The Skill alone does not include the engine.')


PROJECT_ROOT = project_root()
BACKEND = PROJECT_ROOT / 'engine'
PINS = {
    'native_fonts.py': 'ed23b1db6b5cfd225a14100e04d5a62a947f02882dc3b4f31eb62fed43996995',
    'runtime_profiles.py': 'ac82a006b55de6d98fd3d62a16432e8135a4c5672cddc27b3ce895c0dce4dcd4',
    'jy14_headless.py': '122ec4a8cd31c961448465451ea911daed87769fcfe639604c57a7d2a2c7b0be',
    'native_motion.py': '5d743caaa38c921779166e5663d36f72a0c3fdb130a690ac3942a7adcf62d6c2',
    'native_effects.py': 'c46b2fc9221dd613f220564b752e532f8f3753dd5595aaffc24f41d5236e4e97',
    'native_resources.py': '9bddfbb1cd688cebd69ac49f9bbf63c242522d9666a2ef7b412fe097113f68f2',
    'native_visual_effects.py': '15df7e56cc7d575a552c180e72ec712f136c618d271b2f3ad2d32dd5929e844c',
    'native-resource-catalog.json': '97af2df27463a9183fb1aa8f2ef534b37a644cb196f340fe88fdc50b456abde9',
    'native_compound.py': '3b173a3ce10e79e48c0f598b8fbb96bbf35d706db6039a0f68a9917b1717352f',
    'compound-blueprint.json': '9cba9435053280abf9072d5eaccb8586c841b11dac6854b32daf9cbdba76af8e',
    'native_edit.py': 'f5125bda3c3e3bd0a8e96046b51a0cf3bc5bcc53c836421eabde6ec075377d11',
    'native_export.py': '10191828c86c12396c77be5ac7a39ee712c4b5f1ac341a09f73418eac5d7202d',
    'ui_export.py': '2031103bf756c2823a3856715b096b6ff224d1e0f74458ab6c6e9f800cb66d65',
    'native_export.cpp': 'c60da6c65f5bb7ac733b8f5b619401be3921f9254b953a55903d4e7566156379',
    'headless_runtime.py': 'e26cbfc52589cbab7092174b8a8dd8be2b3a753f3c3e95cc589cb2083e5e43d0',
    'blueprint.json': '91f7eddad5bff9af23eb88b53713c180e3e3d4054edd469140cfa9aa56bc1dc9',
    'windows_portable.py': '707e5f1040ad59384f864e5e2ad41ff2c93853be8c7bd562d44f6fb632d244ca',
    'windows_export.py': 'b4f20ce94b6ca0a72d5c542bc56ce9fd23a13a09826ba71a34beb99e23474fc8',
    'ffmpeg_graph.py': 'bc0d897993f9e7c2c5f6c0233a3002c07e235323da20fe0eca2755f1410aa594',
    'ffmpeg_tools.py': 'c8d0817c57573e0e755f3277466fa13e08bdc588d90471344faaf30438e9992f',
}

for name, expected in PINS.items():
    path = BACKEND / name
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit('Headless component changed or unavailable; reverify before updating the pin: ' + name)

sys.path.insert(0, str(BACKEND))
command = sys.argv[1] if len(sys.argv) > 1 else None
if command in {None, '--help', '-h'}:
    print("""M5 Jianying: exact-runtime local drafts and editor-dialog export acceptance.
  doctor | build --plan PLAN --out NEW_BUILD | verify-build --build BUILD
  publish --build BUILD --audit NEW_AUDIT | verify --build BUILD
  edit inspect --draft SOURCE --out INSPECTION
  edit build --plan PLAN --out NEW_BUILD
  edit verify-build | publish | verify  (same --build/--audit options)
  ui-export plan --build BUILD --out NEW_JOB
  ui-export verify --job JOB [--video FILE] [--report NEW_REPORT]
Use COMMAND --help for backend options. Editing always builds a separate copy.
UI export renders in the editor; plan/verify do not operate the UI.
Native ExportService, compounds and Windows are unavailable through this entry.""")
    raise SystemExit(0)
if os.name == 'nt':
    raise SystemExit('M5 local entry requires Apple Silicon macOS')
from runtime_profiles import M5_PROFILE, validate_command
try:
    validate_command(command, M5_PROFILE)
except ValueError as exc:
    raise SystemExit(str(exc)) from None
entrypoint = 'jy14_headless.py'
if command in {'edit', 'ui-export'}:
    allowed = {'inspect', 'build', 'verify-build', 'publish', 'verify'} if command == 'edit' else {'plan', 'verify'}
    nested = sys.argv[2] if len(sys.argv) > 2 else None
    if nested in {None, '--help', '-h'}:
        print(command + ': ' + ', '.join(sorted(allowed)) + '; use SUBCOMMAND --help for options')
        raise SystemExit(0)
    if nested not in allowed:
        raise SystemExit('Unsupported ' + command + ' command; allowed: ' + ', '.join(sorted(allowed)))
    entrypoint = 'native_edit.py' if command == 'edit' else 'ui_export.py'
    del sys.argv[1]
import headless_runtime
try:
    validate_command(command, headless_runtime.doctor()['runtime_profile'])
except ValueError as exc:
    raise SystemExit(str(exc)) from None
runpy.run_path(str(BACKEND / entrypoint), run_name='__main__')
