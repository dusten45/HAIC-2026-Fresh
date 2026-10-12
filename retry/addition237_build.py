"""Build one237 package from retained232 ZIP plus frozen fullDEV addition NPZ."""
import argparse
import hashlib
from pathlib import Path
import zipfile
import numpy as np


def build(base, model, activation, output):
    assert activation in ['identity','tanh']
    m=np.load(model);assert m['weights'].shape==(17,2) and m['theta'].shape==(78,)
    with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
    assert members['agent.py']==Path(__file__).with_name('submission232_agent.py').read_bytes()
    members['retry/nominal237_base.py']=members['agent.py']
    members['agent.py']=Path(__file__).with_name('addition237_agent.py').read_bytes()
    members['retry/addition237_model.py']=('"""Frozen learned addition only, no rawdata/roadidentities."""\nimport numpy as np\nTHETA=np.array('+repr(m['theta'].tolist())+',dtype=np.float64)\nACTIVATION='+repr(activation)+'\n').encode()
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(members.items()):
            assert not name.startswith('/') and '..' not in Path(name).parts
            item=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,data)
    return dict(archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()})


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for n in ['base','model','output']:a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--activation',choices=['identity','tanh'],required=True);p=a.parse_args();print(build(p.base,p.model,p.activation,p.output))
