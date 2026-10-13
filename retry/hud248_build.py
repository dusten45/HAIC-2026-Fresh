"""Install the single 22-input head into a copy of current240, preserving scales."""
import ast,hashlib,zipfile
from pathlib import Path
import numpy as np
from retry.submission232_build import FORBIDDEN


def build(base,model,output):
    with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
    original=dict(members);params=np.load(model)
    assert params['mean'].shape==(22,) and params['weights'].shape==(23,2)
    members['retry/nominal248_source.py']=members['retry/nominal238_base.py']
    members['retry/nominal238_base.py']=Path(__file__).with_name('hud248_agent.py').read_bytes()
    members['retry/hud248_features.py']=Path(__file__).with_name('hud248_features.py').read_bytes()
    constants='"""One frozen TRAIN-only head; no research data or road identities."""\nimport numpy as np\n'
    for k,n in [('mean','HEAD_MEAN'),('std','HEAD_STD'),('weights','HEAD_WEIGHTS')]:constants+=n+'=np.array('+repr(params[k].tolist())+',dtype=np.float64)\n'
    members['retry/hud248_model.py']=constants.encode()
    assert members['agent.py']==original['agent.py'] and members['retry/scale238_model.py']==original['retry/scale238_model.py']
    assert all(members[n]==v for n,v in original.items() if n!='retry/nominal238_base.py')
    for n,v in members.items():
        if not n.endswith('.py'):continue
        for node in ast.walk(ast.parse(v,filename=n)):
            if isinstance(node,ast.Import):assert all(x.name.split('.')[0] not in FORBIDDEN for x in node.names)
            if isinstance(node,ast.ImportFrom):assert (node.module or '').split('.')[0] not in FORBIDDEN
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in ['open','exec','eval','compile','__import__']
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,v in sorted(members.items()):
            info=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,v)
    output.chmod(0o600)
    return dict(archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(v).hexdigest() for n,v in members.items()},base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),original_nominal_preserved=True,global_scales_byte_exact=True,static_boundary_passed=True)
