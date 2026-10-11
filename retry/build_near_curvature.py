"""Restore the original curvature term only at the existing near-hazard branch."""
import argparse
import ast
import hashlib
from pathlib import Path
import zipfile


CHANGES = {
    'retry/parameter_agent.py': [
        (b'def action_target(self, x, forward, speed):',
         b'def action_target(self, x, forward, speed, curvature_offset=0.0):'),
        (b'self.lateral_acceleration / max(abs(curvature), 1e-6)',
         b'self.lateral_acceleration / (abs(curvature) + curvature_offset if curvature_offset else max(abs(curvature), 1e-6))'),
    ],
    'retry/schedule_agent.py': [
        (b'return self.controller.action_target(float(target[0]), float(target[1]), speed)',
         b'return self.controller.action_target(float(target[0]), float(target[1]), speed, curvature_offset=0.003 if near else 0.0)'),
    ],
}


def build(source, destination):
    destination = Path(destination)
    assert not destination.exists()
    with zipfile.ZipFile(source) as original:
        assert len(original.namelist()) == len(set(original.namelist()))
        patched = {}
        for name, replacements in CHANGES.items():
            data = original.read(name)
            for before, after in replacements:
                assert data.count(before) == 1 and after not in data
                data = data.replace(before, after)
            ast.parse(data)
            restored = data
            for before, after in reversed(replacements):
                restored = restored.replace(after, before)
            assert restored == original.read(name)
            patched[name] = data
        with zipfile.ZipFile(destination, 'x') as candidate:
            candidate.comment = original.comment
            for member in original.infolist():
                candidate.writestr(member, patched.get(member.filename, original.read(member.filename)))
    destination.chmod(0o600)
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(destination) as new:
        assert sorted(n for n in old.namelist() if old.read(n) != new.read(n)) == sorted(CHANGES)
    return {'archive_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'changed_members': sorted(CHANGES), 'existing_near_predicate_changed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    print(build(args.source, args.destination))
