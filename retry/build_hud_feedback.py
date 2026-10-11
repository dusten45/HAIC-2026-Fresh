"""Change only pedal speed feedback to a source-defined HUD bar decoder.

Templates come from the official indicator raster and resize pipeline. The
builder accepts a JSON object with a 'templates' map of 18-byte pixel hex keys
to speed-bin midpoints; no observation records are copied to the archive.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile


CHANGES = {
    'retry/parameter_agent.py': [
        (b'def action_target(self, x, forward, speed):',
         b'def action_target(self, x, forward, speed, pedal_speed=None):'),
        (b'        gas = float(np.clip(0.08 * (target - speed), 0, 0.5))\n'
         b'        brake = float(np.clip(0.04 * (speed - target), 0, 0.5))',
         b'        feedback_speed = speed if pedal_speed is None else pedal_speed\n'
         b'        gas = float(np.clip(0.08 * (target - feedback_speed), 0, 0.5))\n'
         b'        brake = float(np.clip(0.04 * (feedback_speed - target), 0, 0.5))'),
    ],
    'retry/schedule_agent.py': [
        (b'from retry.route_agent import route_target',
         b'from retry.route_agent import route_target\nfrom retry.hud_feedback import decode_feedback_speed'),
        (b'return self.controller.action_target(float(target[0]), float(target[1]), speed)',
         b'return self.controller.action_target(float(target[0]), float(target[1]), speed, pedal_speed=decode_feedback_speed(image, speed))'),
    ],
}


def decoder_source(templates):
    assert len(templates) == 65
    assert sorted(templates.values()) == [0.0] + [(i - 0.5) * 2.5 for i in range(1, 65)]
    assert all(len(bytes.fromhex(key)) == 18 for key in templates)
    rows = '\n'.join('    bytes.fromhex(' + repr(key) + '): ' + repr(value) + ','
                     for key, value in sorted(templates.items()))
    return ('''"""Source-raster HUD speed bins for pedal feedback only, with exact matching."""
import numpy as np

TEMPLATES = {
''' + rows + '''
}


def decode_feedback_speed(image, fallback):
    signature = np.rint(image[74:83, 11:13] * 255).astype(np.uint8).tobytes()
    return TEMPLATES.get(signature, fallback)
''').encode()


def build(source, template_path, destination):
    templates = json.loads(Path(template_path).read_text())['templates']
    added = {'retry/hud_feedback.py': decoder_source(templates)}
    for data in added.values():
        ast.parse(data)
    destination = Path(destination)
    with zipfile.ZipFile(source) as old:
        assert len(old.namelist()) == len(set(old.namelist()))
        assert not set(added) & set(old.namelist())
        patched = {}
        for name, changes in CHANGES.items():
            data = old.read(name)
            for before, after in changes:
                assert data.count(before) == 1 and after not in data
                data = data.replace(before, after)
            ast.parse(data)
            restored = data
            for before, after in reversed(changes):
                restored = restored.replace(after, before)
            assert restored == old.read(name)
            patched[name] = data
        with zipfile.ZipFile(destination, 'x') as new:
            new.comment = old.comment
            for member in old.infolist():
                new.writestr(member, patched.get(member.filename, old.read(member.filename)))
            for name, data in added.items():
                member = zipfile.ZipInfo(name, date_time=(2026, 10, 11, 0, 0, 0))
                member.compress_type = zipfile.ZIP_DEFLATED
                member.external_attr = 0o600 << 16
                new.writestr(member, data)
    destination.chmod(0o600)
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(destination) as new:
        assert sorted(name for name in old.namelist() if old.read(name) != new.read(name)) == sorted(CHANGES)
        assert set(new.namelist()) - set(old.namelist()) == set(added)
    return {'archive_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'changed_existing_members': sorted(CHANGES), 'new_members': sorted(added),
            'fitted_parameters': 0, 'route_tracking_near_steering_speed_estimate_unchanged': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--templates', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.templates, args.destination)))
