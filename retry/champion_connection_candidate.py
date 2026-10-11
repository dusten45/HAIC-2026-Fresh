"""Copy only the frozen route-ranking component onto the actual116 archive."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA256 = 'b8c40bcff8ad9eea60e21755950b77235c22a0d7df89eb74f08148bbb0c9890c'
FEATURE_SHA256 = 'c66e2f3bfc42543a8bdcdc821898eb0fd8377ab54929ebcc46708cbee0667d55'
MEMBERS = ['retry/connected_agent.py', 'retry/schedule_agent.py']
BASE_MEMBER_SHA256 = [
    'd2dcfbaf9e6e01c74ba77d4e9a45e3f43fb04c7b9e934756e72e06f695666e38',
    'e60f4b7839bac81c4628e0f79febe67a6da46bcb14d1a6a98d6377804ec41257',
]


def build(base, feature, destination):
    base, feature, destination = map(Path, [base, feature, destination])
    digest = lambda data: hashlib.sha256(data).hexdigest()
    assert digest(base.read_bytes()) == BASE_SHA256
    assert digest(feature.read_bytes()) == FEATURE_SHA256
    with zipfile.ZipFile(base) as original, zipfile.ZipFile(feature) as donor:
        names = original.namelist()
        assert names == donor.namelist() and len(names) == len(set(names))
        before = {n: original.read(n) for n in names}
        assert [digest(before[n]) for n in MEMBERS] == BASE_MEMBER_SHA256
        after = {**before, **{n: donor.read(n) for n in MEMBERS}}
        for name in MEMBERS:
            ast.parse(after[name], filename=name)
        with zipfile.ZipFile(destination, 'x') as output:
            for info in original.infolist():
                output.writestr(info, after[info.filename])
    destination.chmod(0o600)
    with zipfile.ZipFile(destination) as output:
        assert [n for n in names if output.read(n) != before[n]] == MEMBERS
        assert all(output.read(n) == before[n] for n in names if n not in MEMBERS)
    return {'status': 'BUILT_NOT_EXECUTED', 'base116_sha256': BASE_SHA256,
            'feature134_sha256': FEATURE_SHA256,
            'archive_sha256': digest(destination.read_bytes()),
            'changed_members': MEMBERS,
            'unchanged_members': [n for n in names if n not in MEMBERS],
            'members_sha256': {n: digest(data) for n, data in after.items()},
            'source_scope': 'Exact134path-ranking component on actual116; original116detector/tracker preserved.',
            'GT_or_identity_assets': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--feature', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    result = build(args.base, args.feature, args.output)
    with args.receipt.open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    args.receipt.chmod(0o600)
    print(json.dumps({'status': result['status'], 'archive_sha256': result['archive_sha256']}))
