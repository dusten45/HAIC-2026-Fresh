"""Build one immutable final-pedal policy on byte-preserved296 dependencies."""
import hashlib,zipfile
from pathlib import Path
import numpy as np
from retry.path271_run import save,sha
LOW=np.full(6,-np.log(1.25));HIGH=-LOW

def config(p,theta,F):
 theta=np.asarray(theta,np.float64);assert theta.shape==(6,) and np.isfinite(theta).all() and np.all(theta>=LOW) and np.all(theta<=HIGH);G=Path(__file__).resolve().parent.parent
 with zipfile.ZipFile(p['base']['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
 members['retry/speed309_base.py']=members['agent.py'];members['agent.py']=(G/'retry/speed309_agent.py').read_bytes();members['retry/speed309_model.py']=('import numpy as np\nTHETA=np.array('+repr(theta.tolist())+',dtype=np.float64)\n').encode();archive=F/'policy.zip'
 if archive.exists():
  with zipfile.ZipFile(archive) as z:assert set(z.namelist())==set(members) and all(z.read(n)==b for n,b in members.items())
 else:
  with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
   for n,b in sorted(members.items()):item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
  archive.chmod(0o600)
 cfg=dict(p['base'],archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()},worker_path=str(G/'retry/speed309_worker.py'),worker_sha256=sha(G/'retry/speed309_worker.py'));save(F/'candidate-config.json',cfg);return cfg
