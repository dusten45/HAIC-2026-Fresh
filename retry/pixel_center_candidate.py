"""One source-derived obstacle-center inverse on the frozen pixel champion.

Only the existing component center conversion changes. Detector support,
count/order/radius, road path, tracker, route and control are byte-preserved.
The camera-origin constants are image geometry; no research labels enter ZIP.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile


BASE_SHA256 = 'b8c40bcff8ad9eea60e21755950b77235c22a0d7df89eb74f08148bbb0c9890c'
MEMBER = 'retry/clearance_agent.py'
OLD = '            obstacles.append(((float(cx) - 42) / 1.3608, (63 - float(cy)) / 1.701, 1.2))\n'
NEW = '            obstacles.append(((float(cx) - 41.542) / 1.3608, (62.4475 - float(cy)) / 1.701, 1.2))\n'


def build(source, destination):
    source, destination = Path(source), Path(destination)
    digest = lambda data: hashlib.sha256(data).hexdigest()
    assert digest(source.read_bytes()) == BASE_SHA256
    with zipfile.ZipFile(source) as original:
        names = original.namelist()
        assert len(names) == len(set(names))
        before = {name: original.read(name) for name in names}
        text = before[MEMBER].decode()
        assert text.count(OLD) == 1
        changed = text.replace(OLD, NEW).encode()
        ast.parse(changed, filename=MEMBER)
        after = {**before, MEMBER: changed}
        with zipfile.ZipFile(destination, 'x') as output:
            for info in original.infolist():
                output.writestr(info, after[info.filename])
    destination.chmod(0o600)
    with zipfile.ZipFile(destination) as output:
        assert output.namelist() == names
        assert [name for name in names if output.read(name) != before[name]] == [MEMBER]
    origin = [(500 + .5) * 84 / 1000 - .5, (599 + .5) * 84 / 800 - .5]
    assert origin == [41.542, 62.4475]
    return {'status': 'BUILT_NOT_EXECUTED', 'base_sha256': BASE_SHA256,
            'archive_sha256': digest(destination.read_bytes()),
            'members_sha256': {name: digest(data) for name, data in after.items()},
            'changed_members': [MEMBER], 'old_obstacle_origin_xy': [42, 63],
            'new_obstacle_origin_xy': origin,
            'body_center_delta_m': [(42 - origin[0]) / 1.3608, (origin[1] - 63) / 1.701],
            'unchanged_members': [name for name in names if name != MEMBER],
            'GT_or_identity_data_in_candidate': False,
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
    print(json.dumps({'status': receipt['status'], 'archive_sha256': receipt['archive_sha256']}))
