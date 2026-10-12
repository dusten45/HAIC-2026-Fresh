"""Build the frozen231 submission ZIP from the retained nominal archive.

python -m retry.submission232_build --base BASE.zip \
  --parameters retry/single231_parameters.json --output OUTPUT.zip
No simulator, data collection, training or submission is performed.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile

FORBIDDEN = {'ctypes','importlib','multiprocessing','os','pathlib','resource','shutil',
             'signal','socket','subprocess','sys','core','env_wrapper','gym','gymnasium','Box2D'}


def build(base, parameters, output):
    params = json.loads(parameters.read_text())
    assert params['schema'] == 'normal24-affine-pedal-v1'
    assert params['settings']['L2_lambda'] == 1 and params['settings']['residual_clip'] == .5
    with zipfile.ZipFile(base) as z:
        members = {n: z.read(n) for n in z.namelist()}
    assert members['agent.py'].decode() == ('from retry.schedule_agent import HazardScheduledAgent\n\n'
        'class Agent(HazardScheduledAgent):\n    def __init__(self):\n'
        '        super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 8.0)\n')
    members['agent.py'] = Path(__file__).with_name('submission232_agent.py').read_bytes()
    model = '"""Frozen231 learned parameters only; no raw data or road identities."""\nimport numpy as np\n'
    for key, name in [('mean','HEAD_MEAN'),('std','HEAD_STD'),('weights','HEAD_WEIGHTS')]:
        model += name+' = np.array('+repr(params[key])+', dtype=np.float64)\n'
    members['retry/submission232_model.py'] = model.encode()
    for name, data in members.items():
        assert not name.startswith('/') and '..' not in Path(name).parts
        assert name.endswith(('.py',)) or name == 'LICENSE'
        if not name.endswith('.py'): continue
        tree = ast.parse(data, filename=name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): assert all(a.name.split('.')[0] not in FORBIDDEN for a in node.names), name
            if isinstance(node, ast.ImportFrom): assert (node.module or '').split('.')[0] not in FORBIDDEN, name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {'compile','eval','exec','__import__','open'}, name
    assert not output.exists()
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(members.items()):
            item = zipfile.ZipInfo(name, date_time=(2026,10,9,0,0,0))
            item.compress_type = zipfile.ZIP_DEFLATED;item.external_attr = 0o100644 << 16
            z.writestr(item, data)
    with zipfile.ZipFile(output) as z:
        assert len(z.infolist()) < 1000 and sum(i.file_size for i in z.infolist()) < 2_000_000_000
        assert all(i.file_size <= 500_000_000 and i.file_size/max(1,i.compress_size) <= 100 for i in z.infolist())
    assert output.stat().st_size <= 500_000_000
    return dict(archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        members_sha256={n:hashlib.sha256(d).hexdigest() for n,d in members.items()},
        parameter_sha256=hashlib.sha256(parameters.read_bytes()).hexdigest(),
        base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
        bytes=output.stat().st_size,files=len(members),static_boundary_passed=True)


if __name__ == '__main__':
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--base',type=Path,required=True);a.add_argument('--parameters',type=Path,required=True)
    a.add_argument('--output',type=Path,required=True);p=a.parse_args()
    print(json.dumps(build(p.base,p.parameters,p.output),indent=2))
