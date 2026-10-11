"""Match the frozen pixel-center candidate's optical memory coordinate frame.

Only both directions of the affine pixel/body roundtrip change. Optical-flow
estimation, fallback motion, detection, age, merge, routing and control remain.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA256 = '3a18f8182003358c0ba3257b0b20696584850961af6a4d3c4818a36d0e3f89fb'
MEMBER = 'retry/temporal_agent.py'
OLD = '''                pixel = transform @ np.array([42 + 1.3608 * x, 63 - 1.701 * y, 1])
                x, y = (pixel[0] - 42) / 1.3608, (63 - pixel[1]) / 1.701
'''
NEW = '''                pixel = transform @ np.array([41.542 + 1.3608 * x, 62.4475 - 1.701 * y, 1])
                x, y = (pixel[0] - 41.542) / 1.3608, (62.4475 - pixel[1]) / 1.701
'''


def build(source, destination):
    source, destination = Path(source), Path(destination)
    digest = lambda b: hashlib.sha256(b).hexdigest()
    assert digest(source.read_bytes()) == BASE_SHA256
    with zipfile.ZipFile(source) as original:
        names = original.namelist()
        assert len(names) == len(set(names))
        before = {name: original.read(name) for name in names}
        text = before[MEMBER].decode()
        assert text.count(OLD) == 1
        after = {**before, MEMBER: text.replace(OLD, NEW).encode()}
        ast.parse(after[MEMBER], filename=MEMBER)
        with zipfile.ZipFile(destination, 'x') as output:
            for info in original.infolist():
                output.writestr(info, after[info.filename])
    destination.chmod(0o600)
    with zipfile.ZipFile(destination) as output:
        assert output.namelist() == names
        assert [n for n in names if output.read(n) != before[n]] == [MEMBER]
    return {'status': 'BUILT_NOT_EXECUTED', 'base_sha256': BASE_SHA256,
            'archive_sha256': digest(destination.read_bytes()),
            'changed_members': [MEMBER], 'unchanged_members': [n for n in names if n != MEMBER],
            'members_sha256': {n: digest(b) for n, b in after.items()},
            'old_memory_origin_xy': [42, 63], 'new_memory_origin_xy': [41.542, 62.4475],
            'GT_or_identity_data_in_candidate': False, 'new_environment_policy_model_calls': 0}


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
    print(json.dumps({'status': receipt['status'], 'archive_sha256': receipt['archive_sha256']}))
