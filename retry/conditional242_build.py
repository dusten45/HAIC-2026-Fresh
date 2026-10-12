"""Build fixed242 basis/coefficients over retained240 package, no data included."""
import hashlib
from pathlib import Path
import zipfile
import numpy as np


def build(base,theta,output):
    t=np.asarray(theta,float);assert t.shape==(2,) and np.all(np.abs(t)<=np.log(1.5))
    with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
    assert members['agent.py']==Path(__file__).with_name('scale238_agent.py').read_bytes()
    members['retry/nominal242_base.py']=members['agent.py'];members['agent.py']=Path(__file__).with_name('conditional242_agent.py').read_bytes()
    members['retry/conditional242_model.py']=('"""Two fixedcoefficients, no rawdata/roadidentities."""\nimport numpy as np\nTHETA=np.array('+repr(t.tolist())+',dtype=np.float64)\n').encode()
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(members.items()):
            item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
    return dict(archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()})
