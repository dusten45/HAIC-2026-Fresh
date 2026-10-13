"""Install a once-only scalar goal selector into the identity-verified264 plumbing."""
import ast,hashlib,zipfile
from pathlib import Path
import numpy as np
from retry.submission232_build import FORBIDDEN

def build(base,model,output,identity=False):
 with zipfile.ZipFile(base) as z:original={n:z.read(n) for n in z.namelist()}
 members=dict(original);nominal=members['retry/nominal238_base.py'].decode();control=members['retry/parameter_agent.py'].decode()
 nominal=nominal.replace('from retry.submission232_model import','from retry.pace270_target import choose\nfrom retry.submission232_model import',1)
 nominal=nominal.replace('    def correct_pedals(self, features, nominal):','    def reset(self, observation):\n        super().reset(observation);self.pace270_first=True\n\n    def correct_pedals(self, features, nominal):',1)
 nominal=nominal.replace('        image = observation[-1]',"        self.last_plan=dict(active=False,fallback=True,reason='absent_goal',planner_ms=0.,pace_calls=0,steering_unchanged=True,nominal_memory_preserved=True)\n        image = observation[-1]",1)
 needle='            nominal = np.asarray(self.controller.action_target(x, forward, speed, pedal_speed=feedback), np.float32)';assert nominal.count(needle)==1
 replacement='''            original_nominal = np.asarray(self.controller.action_target(x, forward, speed, pedal_speed=feedback, update_memory=False), np.float32)
            original_features = [0., x, forward, speed, feedback, curvature, target_speed,
                previous_steer, float(self.controller.lateral_acceleration == self.lateral_safe),
                length, float(len(path)), float(len(obstacles)),
                min((float(np.hypot(ox, oy)) for ox, oy, _ in obstacles), default=100.),
                *map(float, original_nominal)]
            self.pace270_original_features=original_features
            target_speed = choose(self, original_features)
            nominal = np.asarray(self.controller.action_target(x, forward, speed, pedal_speed=feedback, target_speed_override=target_speed), np.float32)'''
 nominal=nominal.replace(needle,replacement,1)
 control=control.replace('def action_target(self, x, forward, speed, pedal_speed=None):','def action_target(self, x, forward, speed, pedal_speed=None, target_speed_override=None, update_memory=True):',1).replace('        self.previous_steer = steer','        if update_memory:self.previous_steer = steer',1)
 needle='        feedback_speed = speed if pedal_speed is None else pedal_speed';control=control.replace(needle,'        if target_speed_override is not None:target=float(target_speed_override)\n'+needle,1)
 members['retry/nominal238_base.py']=nominal.encode();members['retry/parameter_agent.py']=control.encode();members['retry/pace270_target.py']=Path(__file__).with_name('pace270_target.py').read_bytes();params=np.load(model)
 text='import numpy as np\nWEIGHTS=np.array('+repr(params['weights'].tolist())+',dtype=np.float64)\nLOG_MIN='+repr(float(params['log_min']))+'\nLOG_MAX='+repr(float(params['log_max']))+'\n';members['retry/scalar270_model.py']=text.encode();members['retry/mode270.py']=('SAME_TARGET='+repr(identity)+'\n').encode()
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
 return dict(type='champion',archive_path=str(output),archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(d).hexdigest() for n,d in members.items()},assets={},constants={},identity=identity,root_head_scales_perception_byte_exact=True,static_boundary_passed=True)
