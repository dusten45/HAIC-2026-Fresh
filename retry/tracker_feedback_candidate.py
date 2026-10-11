"""Use the frozen HUD decoder for fallback memory displacement only.

The base already has consistent optical memory origins. Current detection,
flow, lifetime, route, lookahead and control source are byte-preserved.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA256 = '6c1f87a9d5a19e67a85cc8c8b6a129720e9176dcc9644782d7775f8b6178d8c3'
MEMBER = 'retry/temporal_agent.py'
OLD_IMPORT = 'from retry.clearance_agent import road_and_obstacles\n'
NEW_IMPORT = OLD_IMPORT + 'from retry.hud_feedback import decode_feedback_speed\n'
OLD = '                y -= speed * 0.08\n'
NEW = '                y -= decode_feedback_speed(image, speed) * 0.08\n'


def build(source, destination):
    source, destination = Path(source), Path(destination)
    digest = lambda b: hashlib.sha256(b).hexdigest()
    assert digest(source.read_bytes()) == BASE_SHA256
    with zipfile.ZipFile(source) as original:
        names = original.namelist()
        assert len(names) == len(set(names))
        before = {n: original.read(n) for n in names}
        text = before[MEMBER].decode()
        assert text.count(OLD_IMPORT) == text.count(OLD) == 1
        changed = text.replace(OLD_IMPORT, NEW_IMPORT).replace(OLD, NEW).encode()
        ast.parse(changed, filename=MEMBER)
        after = {**before, MEMBER: changed}
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
            'single_change': 'Existing fixed HUD decoder in fallback tracking displacement only',
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
