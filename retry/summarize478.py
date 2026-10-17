"""Derived aggregate/public closure from private478 saved analysis."""
import json,math,sys,datetime
from pathlib import Path
from retry.audit475_forces import read,put,sha,G

def run(root):
 d=root/'stage478';result=read(d/'result.json');rows=read(d/'rows-private.json');public=json.loads(json.dumps(result))
 for q in public['selected']:
  source=rows[q['action']-1];q['rear_omega_before_mean']=sum(w['omega'] for w in source['wheel_before'] if w['wheel']>=2)/2;q['local_normal_velocity_m_s']=q['start']['speed']*math.sin(q['start']['course_error']);q['local_normal_velocity_is_not_future_prediction']=True
  for key in ['first_axles','last_axles']:
   for axle,a in q[key].items():
    for field,values in list(a.items()):
     if isinstance(values,list):
      a.pop(field);a[field+('_abs_max' if 'slip' in field else '_mean')]=max(abs(x) for x in values) if 'slip' in field else sum(values)/len(values)
 public['raw_source_wheel_arrays_public']=False;public['full_wheel_arrays_private_single_analysis_raw']=True
 public['mechanism_limits']=['All7interventions gas-only, not brake removal; no causal proof that more braking alone would fix','first47 and69 started with comparable slip but different speed/steer/yaw evolution','70-74 gas remainednear0 yet lateral slip initiallygrew; not renewedgasramp explanation','74Mfallsto0 afterheading/course error accrued; lowinstantaneousforce demand is not path recovery','reference scalar reproduces74nominals but does not certify lateral feasibility']
 (G/'retry/audit478_result.json').write_text(json.dumps(public,indent=2)+'\n')
 put(root/'stage478-summary-source-private.json',dict(stage=478,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=sha(Path(__file__)),input_result_sha256=sha(d/'result.json'),input_rows_sha256=sha(d/'rows-private.json'),public_aggregate_sha256=sha(G/'retry/audit478_result.json'),new_physics=0,new_native=0))
 print(json.dumps(public['conclusions']))
if __name__=='__main__':run(Path(sys.argv[1]))
