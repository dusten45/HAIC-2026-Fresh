"""Six bounded relative log parameters at240's original execution locations."""
from pathlib import Path
import hashlib,zipfile
import numpy as np
LOW=np.r_[np.repeat(np.log(.8),5),np.log(40/45)]
HIGH=np.r_[np.repeat(np.log(1.25),5),np.log(50/45)]
def build(base,theta,output):
 t=np.asarray(theta,np.float64);assert t.shape==(6,) and np.all(t>=LOW) and np.all(t<=HIGH)
 with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
 ns={};exec(members['retry/scale238_model.py'],ns);scales=np.asarray(ns['SCALES'],np.float64)*np.exp(t[:2])
 # root agent.py remains exact: frozen head clip, then scales, then final clip.
 members['retry/scale238_model.py']=('import numpy as np\nSCALES=np.array('+repr(scales.tolist())+',dtype=np.float64)\n').encode()
 vals=np.exp(t);members['retry/cem294_constants.py']=('STEERING_GAIN='+repr(float(vals[2]))+'\nLOOKAHEAD_SCALE='+repr(float(vals[3]))+'\nLATERAL_SCALE='+repr(float(vals[4]))+'\nCEILING='+repr(float(45*vals[5]))+'\n').encode()
 s=members['retry/parameter_agent.py'].decode();old='np.arctan(3.24 * curvature)';assert s.count(old)==1;s=s.replace('import numpy as np','import numpy as np\nfrom retry.cem294_constants import STEERING_GAIN');s=s.replace(old,'np.arctan(3.24 * curvature * STEERING_GAIN)');members['retry/parameter_agent.py']=s.encode()
 s=members['retry/route_agent.py'].decode();assert s.count('def route_target(path, speed):')==1;s=s.replace('def route_target(path, speed):','def route_target(path, speed, scale=1.0):');s=s.replace('remaining = float(np.clip(4 + 0.35 * speed, 6, 14))','remaining = float(np.clip((4 + 0.35 * speed) * scale, 6 * scale, 14 * scale))');members['retry/route_agent.py']=s.encode()
 s=members['retry/nominal238_base.py'].decode();s=s.replace('import numpy as np','import numpy as np\nfrom retry.cem294_constants import LOOKAHEAD_SCALE, LATERAL_SCALE, CEILING');assert s.count('45.0, 24.0, 8.0')==1;s=s.replace('45.0, 24.0, 8.0','CEILING, 24.0 * LATERAL_SCALE, 8.0 * LATERAL_SCALE');assert s.count('target = route_target(path, speed)')==1;s=s.replace('target = route_target(path, speed)','target = route_target(path, speed, LOOKAHEAD_SCALE)');members['retry/nominal238_base.py']=s.encode()
 with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(members.items()):
   item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
 Path(output).chmod(0o600)
 return dict(archive_path=str(output),archive_sha256=hashlib.sha256(Path(output).read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()},theta=t.tolist(),scales=scales.tolist(),ceiling=float(45*vals[5]))
