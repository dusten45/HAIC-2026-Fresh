"""Build one fixed extra-pixel routing margin on the frozen HUD champion.

Perception, tracker, route target and controller bytes are preserved. This is a
single fixed falsification setting, not a threshold-search interface.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile


BASE_SHA256 = 'b8c40bcff8ad9eea60e21755950b77235c22a0d7df89eb74f08148bbb0c9890c'
MEMBER = 'retry/connected_agent.py'


def build(source, destination):
    source, destination = Path(source), Path(destination)
    digest = lambda data: hashlib.sha256(data).hexdigest()
    assert digest(source.read_bytes()) == BASE_SHA256
    with zipfile.ZipFile(source) as original:
        names = original.namelist()
        assert len(names) == len(set(names))
        before = {name: original.read(name) for name in names}
        old = '        clearance = 2.6 + radius\n'
        new = '        clearance = 2.6 + radius + 1.0 / 1.3608\n'
        text = before[MEMBER].decode()
        assert text.count(old) == 1
        changed = text.replace(old, new).encode()
        ast.parse(changed, filename=MEMBER)
        after = {**before, MEMBER: changed}
        with zipfile.ZipFile(destination, 'x') as output:
            for info in original.infolist():
                output.writestr(info, after[info.filename])
    destination.chmod(0o600)
    with zipfile.ZipFile(destination) as output:
        assert output.namelist() == names
        assert [name for name in names if output.read(name) != before[name]] == [MEMBER]
    return {'status': 'BUILT_NOT_EXECUTED', 'base_sha256': BASE_SHA256,
            'archive_sha256': digest(destination.read_bytes()),
            'members_sha256': {name: digest(data) for name, data in after.items()},
            'changed_members': [MEMBER], 'extra_route_margin_m': 1.0 / 1.3608,
            'unchanged_members': [name for name in names if name != MEMBER],
            'new_environment_policy_model_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    receipt = build(args.source, args.output)
    with args.receipt.open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    args.receipt.chmod(0o600)
    print(json.dumps({'status': receipt['status'],
                      'archive_sha256': receipt['archive_sha256'],
                      'extra_route_margin_m': receipt['extra_route_margin_m']}))
