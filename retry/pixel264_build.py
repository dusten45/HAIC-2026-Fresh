"""Connect immutable263 profile to one240 goal-selection point with explicit plumbing."""
import ast,hashlib,zipfile
from pathlib import Path
from retry.submission232_build import FORBIDDEN

def build(base,output,identity=False):
 with zipfile.ZipFile(base) as z:original={n:z.read(n) for n in z.namelist()}
 members=dict(original);nominal=members['retry/nominal238_base.py'].decode();control=members['retry/parameter_agent.py'].decode()
 nominal=nominal.replace('from retry.submission232_model import','from retry.pixel264_target import select_target_speed\nfrom retry.submission232_model import',1)
 nominal=nominal.replace('        image = observation[-1]', "        self.last_plan=dict(active=False,fallback=True,identity=False,planner_ms=0.,steering_unchanged=True,nominal_memory_preserved=True)\n        image = observation[-1]",1)
 needle='            nominal = np.asarray(self.controller.action_target(x, forward, speed, pedal_speed=feedback), np.float32)';assert nominal.count(needle)==1
 nominal=nominal.replace(needle,'            target_speed = select_target_speed(self,path,feedback,forward,target_speed,obstacles)\n            nominal = np.asarray(self.controller.action_target(x, forward, speed, pedal_speed=feedback, target_speed_override=target_speed), np.float32)',1)
 control=control.replace('def action_target(self, x, forward, speed, pedal_speed=None):','def action_target(self, x, forward, speed, pedal_speed=None, target_speed_override=None):',1)
 needle='        feedback_speed = speed if pedal_speed is None else pedal_speed';assert control.count(needle)==1
 control=control.replace(needle,'        if target_speed_override is not None:target=float(target_speed_override)\n'+needle,1)
 members['retry/nominal238_base.py']=nominal.encode();members['retry/parameter_agent.py']=control.encode();members['retry/pixel264_target.py']=Path(__file__).with_name('pixel264_target.py').read_bytes()
 frozen=Path(__file__).with_name('pixel263_agent.py').read_text();constants=frozen.split('# Source-derived vehicle constants',1)[1].split('\n\nclass Agent',1)[0];members['retry/profile263_frozen.py']=('"""Exact frozen263 numerical profile; no actuator output or runtimeGT."""\nimport numpy as np\n# Source-derived vehicle constants'+constants).encode();members['retry/mode264.py']=('SAME_TARGET='+repr(bool(identity))+'\n').encode()
 assert all(members[n]==v for n,v in original.items() if n not in ['retry/nominal238_base.py','retry/parameter_agent.py'])
 for name,data in members.items():
  if not name.endswith('.py'):continue
  for node in ast.walk(ast.parse(data,filename=name)):
   if isinstance(node,ast.Import):assert all(x.name.split('.')[0] not in FORBIDDEN for x in node.names)
   if isinstance(node,ast.ImportFrom):assert (node.module or '').split('.')[0] not in FORBIDDEN
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in {'open','exec','eval','compile','__import__'}
 with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for name,data in sorted(members.items()):
   item=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,data)
 output.chmod(0o600)
 return dict(type='champion',archive_path=str(output),archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(d).hexdigest() for n,d in members.items()},assets={},constants={},identity=identity,root_head_scales_and_perception_byte_exact=True,static_boundary_passed=True)
