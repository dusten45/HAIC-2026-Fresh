"""Build a fixed two-scale238 package, excluding all research data."""
import hashlib
from pathlib import Path
import zipfile
import numpy as np


def build(base,theta,output):
    t=np.asarray(theta,float);assert t.shape==(2,) and np.all(np.abs(t)<=np.log(1.5))
    with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
    assert members['agent.py']==Path(__file__).with_name('submission232_agent.py').read_bytes()
    members['retry/nominal238_base.py']=members['agent.py'];members['agent.py']=Path(__file__).with_name('scale238_agent.py').read_bytes()
    members['retry/scale238_model.py']=('"""Two frozen global scale constants only."""\nimport numpy as np\nSCALES=np.array('+repr(np.exp(t).tolist())+',dtype=np.float64)\n').encode()
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(members.items()):
            item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
    return dict(archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()})
