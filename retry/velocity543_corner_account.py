"""Reproduce saved541 descriptive curvature account; no simulation calls."""
from pathlib import Path
import json,math,bisect,time

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response541-private');full=json.loads((D/'native-full-records-private.json').read_text());split=51+sum(x['raw_ticks'] for x in full[0]['rows']);path=json.loads((D/'frozen-paths-private.json').read_text())['candidate'];rr=[json.loads(p.read_text()) for p in sorted(D.glob('raw-*.json'))][split:];groups={}
 for label,lo,hi in [('firstcorner',25,44),('firstexit_and_fast',45,80),('middlecorner',100,124),('latecorner',140,160)]:
  rows=[r for r in rr if r['phase']=='action' and lo<=r['action']<=hi];data=[]
  for r in rows:
   a=r['before']['velocity'];b=r['velocity'];speed=(math.hypot(*a)+math.hypot(*b))/2;turn=math.atan2(a[0]*b[1]-a[1]*b[0],sum(a[j]*b[j] for j in range(2)));kactual=turn/(.02*speed);i=max(0,min(len(path['ds'])-1,bisect.bisect_left(path['arcs'][1:],r['station'])));kref=path['curvature'][i];data.append((kactual,kref,r['path_error'],r['margin']))
  groups[label]=dict(mean_abs_actual_velocity_curvature_1_m=sum(abs(x[0]) for x in data)/len(data),mean_abs_reference_discrete_curvature_1_m=sum(abs(x[1]) for x in data)/len(data),mean_abs_curvature_mismatch_1_m=sum(abs(x[0]-x[1]) for x in data)/len(data),max_path_error_m=max(x[2] for x in data),minimum_footprint_margin_m=min(x[3] for x in data))
 out=dict(status='SAVED541_DESCRIPTIVE_CORNER_ACCOUNT',groups=groups,method='Actual20msvelocity-directionturn/(dt*meanCOMspeed) versus frozenpath discretecurvature atcurrentownstation; descriptive, referencepolygon nodes are not instantaneous vehiclecurvature targets. No causal/laptime attribution, no root/gate changes.',new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/velocity543_corner_account.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
