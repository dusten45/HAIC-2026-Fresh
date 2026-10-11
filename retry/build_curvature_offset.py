"""Remove one additive curvature term from an immutable policy archive.

This changes only the active speed-target denominator. The global speed ceiling,
lateral acceleration schedule, steering and pedal feedback laws stay fixed.
The numerical purpose of the original additive term is not assumed.
"""
import argparse
import hashlib
from pathlib import Path
import zipfile


MEMBER = 'retry/parameter_agent.py'
BEFORE = b'self.lateral_acceleration / (abs(curvature) + 0.003)'
AFTER = b'self.lateral_acceleration / max(abs(curvature), 1e-6)'


def build(source, destination):
    """Preserve ZIP metadata and every other member byte for one fixed test."""
    destination = Path(destination)
    assert not destination.exists()
    with zipfile.ZipFile(source) as original:
        names = original.namelist()
        assert len(names) == len(set(names)) and MEMBER in names
        before = original.read(MEMBER)
        assert before.count(BEFORE) == 1
        after = before.replace(BEFORE, AFTER)
        assert after.replace(AFTER, BEFORE) == before
        with zipfile.ZipFile(destination, 'x') as candidate:
            candidate.comment = original.comment
            for member in original.infolist():
                data = after if member.filename == MEMBER else original.read(member.filename)
                candidate.writestr(member, data)
    destination.chmod(0o600)
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(destination) as candidate:
        changed = [n for n in names if original.read(n) != candidate.read(n)]
        assert changed == [MEMBER]
    return {'changed_member': MEMBER,
            'before_sha256': hashlib.sha256(before).hexdigest(),
            'after_sha256': hashlib.sha256(after).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    print(build(args.source, args.destination))
