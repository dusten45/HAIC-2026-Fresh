"""Once-per-road unchanged258 geometric recipe on the four remaining DEV cases."""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
from retry.racing258_plan import solve
from retry.racing258_feasibility import project
from retry.pace268_profile import multipliers

def run(D):
 p=json.loads((D/'preparation-plan.json').read_text());records=[];error=None
 def save(q,x):q.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');q.chmod(0o600)
 def convert(x):
  if isinstance(x,np.ndarray):return x.tolist()
  if isinstance(x,dict):return {k:convert(v) for k,v in x.items()}
  return x
 assert not (D/'solver-opening.json').exists(),'No repeated road solve'
 for q,h in p['hashes'].items():assert hashlib.sha256(Path(q).read_bytes()).hexdigest()==h
 save(D/'solver-opening.json',dict(epoch=time.time()))
 try:
  for road in p['roads']:
   snapshot=json.loads(Path(p['materializations'][road]).read_text())['snapshots']['1'];tic=time.perf_counter();s=convert(solve(snapshot,p['model']));s['model']=p['model'];s['whole_map_GT']=True;repair=None
   if not s['free_feasible'] and min(s['free_clearance'])>=-.001 and s['free_profile']['max_abs_curvature']<=np.tan(.4)/3.24:
    try:
     z=project(snapshot,s);repair={k:convert(v) for k,v in z.items() if k not in ['line','coefficients','profile','clearance']};s.update(line=convert(z['line']),coefficients=convert(z['coefficients']),free_profile=convert(z['profile']),free_clearance=convert(z['clearance']),free_feasible=True)
    except AssertionError:repair=dict(failed=True)
   s['numerical_projection']=repair;save(D/(road+'-plan-private.json'),s)
   if s['free_feasible']:
    ds=np.array(s['free_profile']['ds']);k=np.array(s['free_profile']['curvature']);v=np.array(s['free_profile']['speed']);assert np.array_equal(v*multipliers([0,0,0],k,ds,p['model']),v*1.5);multipliers(p['coefficients'],k,ds,p['model'])
   r=dict(road=road,feasible=s['free_feasible'],solver_objectives=s['model_calls'],solver_wall_s=s['model_wall_s'],total_planning_wall_s=time.perf_counter()-tic,minimum_clearance_m=float(min(s['free_clearance'])),max_abs_curvature=s['free_profile']['max_abs_curvature'],violation=s['violation'],projection=repair,new_native=0,model_physics_ticks=0,plan_sha256=hashlib.sha256((D/(road+'-plan-private.json')).read_bytes()).hexdigest());records.append(r);save(D/'solver-records.json',records);print(json.dumps(r),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'solver-outcome.json',dict(records=records,technical_error=error,wall_s=time.time()-json.loads((D/'solver-opening.json').read_text())['epoch'],native_actions=0))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--stage-dir',type=Path,required=True);run(a.parse_args().stage_dir.resolve())
