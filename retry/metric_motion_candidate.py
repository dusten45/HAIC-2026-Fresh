"""Fit the existing sparse frame motion in isotropic body coordinates.

Only motion-fit coordinates change. Features, LK, LMEDS, determinant guard,
fixed-HUD fallback, current detections, radius, routing and control are preserved.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA256 = '945f9d04caf5a85efbfd33a7b56f6b8dc0bef688b202a7281659d516ff0c9cc2'
MEMBER = 'retry/temporal_agent.py'
OLD = '''                    candidate, _ = cv2.estimateAffinePartial2D(points[valid], following[valid], method=cv2.LMEDS)
                    if candidate is not None and np.isfinite(candidate).all() and 0.8 <= np.linalg.det(candidate[:, :2]) <= 1.2:
                        transform = candidate
'''
NEW = '''                    origin = np.array([41.542, 62.4475])
                    scale = np.array([1.3608, -1.701])
                    before = (points[valid].reshape(-1, 2) - origin) / scale
                    after = (following[valid].reshape(-1, 2) - origin) / scale
                    candidate, _ = cv2.estimateAffinePartial2D(before, after, method=cv2.LMEDS)
                    if candidate is not None and np.isfinite(candidate).all() and 0.8 <= np.linalg.det(candidate[:, :2]) <= 1.2:
                        linear = np.diag(scale) @ candidate[:, :2] @ np.diag(1 / scale)
                        offset = origin + scale * candidate[:, 2] - linear @ origin
                        transform = np.c_[linear, offset]
'''


def build(source, destination):
    source, destination = Path(source), Path(destination)
    digest = lambda b: hashlib.sha256(b).hexdigest()
    assert digest(source.read_bytes()) == BASE_SHA256
    with zipfile.ZipFile(source) as original:
        names = original.namelist()
        assert len(names) == len(set(names))
        before = {n: original.read(n) for n in names}
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
        assert [n for n in names if output.read(n) != before[n]] == [MEMBER]
    return {'status': 'BUILT_NOT_EXECUTED', 'base_sha256': BASE_SHA256,
            'archive_sha256': digest(destination.read_bytes()),
            'changed_members': [MEMBER], 'unchanged_members': [n for n in names if n != MEMBER],
            'members_sha256': {n: digest(b) for n, b in after.items()},
            'single_change': 'Existing sparse motion fit in isotropic body coordinates, converted to pixel affine',
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
