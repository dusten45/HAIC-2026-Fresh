"""Derive a two-site global-ceiling intervention from an immutable archive.

The fixed Agent argument is active through SpeedController. The legacy base
GeometryController ceiling is overridden in that Agent and has no active effect.
An unused constructor default stays unchanged. No recovery component is added.
"""
import argparse
import hashlib
from pathlib import Path
import zipfile


SITES = {
    'agent.py': (b'-6.545558315185489, 28.0, 7.0, 5.0)',
                 b'-6.545558315185489, {cap}, 7.0, 5.0)'),
    'retry/geometry_agent.py': (b'min(28.0,', b'min({cap},'),
}


def build(source, destination, cap):
    assert cap in (28, 40)
    assert not Path(destination).exists()
    with zipfile.ZipFile(source) as original:
        names = original.namelist()
        assert len(names) == len(set(names)) and set(SITES) <= set(names)
        changed = {}
        with zipfile.ZipFile(destination, 'x') as candidate:
            candidate.comment = original.comment
            for member in original.infolist():
                data = original.read(member.filename)
                before = data
                if member.filename in SITES:
                    old, template = SITES[member.filename]
                    assert data.count(old) == 1, member.filename
                    new = template.replace(b'{cap}', str(float(cap)).encode())
                    data = data.replace(old, new)
                if data != before:
                    changed[member.filename] = {
                        'before': hashlib.sha256(before).hexdigest(),
                        'after': hashlib.sha256(data).hexdigest(),
                    }
                candidate.writestr(member, data)
    Path(destination).chmod(0o600)
    assert set(changed) == (set(SITES) if cap == 40 else set())
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--cap', required=True, type=int, choices=(28, 40))
    arguments = parser.parse_args()
    print(build(arguments.source, arguments.destination, arguments.cap))
