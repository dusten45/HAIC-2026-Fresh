"""Algebraic saved-profile clock and stored actuator diagnostics, no dynamics."""
import datetime,json,hashlib,math,sys,time
from pathlib import Path
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 assert not p.exists(),p
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
def prepare(root):
 d=root/'stage403';fixed=Path(read(root/'stage402/plan.json')['fixed_plan']);paths=[Path(__file__),fixed,root/'stage402/P10_C/trace-private.jsonl',root/'stage402/P10_C/final-full-private.json',root/'stage402/P10_C/initial-private.json',d/'result.json']
 p=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Closed-formpiecewiseWreferenceclock,notvehicleintegration; storednativeaccelerationandactuatorstats. Afterinitialdescriptive403, notcausaltest.',clock='ForpiecewiseWlinearuse2*distance/(r_left+r_right),at0..100%arc. Comparecumulativeclockwithsavedwrappercrossingintervals,notinstantaneousactualtimeinterpolation.',groups='All, rawpositiveaccelclamp, r-v>=5, brakingbelowr. Scoretimeweights; achievednormaccel fromactualpre/postfulldt,gaslagactualrearrawticks. No sourcecapacity/commandcounterfactualinference.',sources={str(f):sha(f) for f in paths},new_native_actor_model_learning_SEALED=0)
 save(d/'supplement-plan.json',p);print('Static clock/actuator supplement registered')
def run(root):
 d=root/'stage403';p=read(d/'supplement-plan.json')
 for f,h in p['sources'].items():assert sha(f)==h
 start,cpu=time.perf_counter(),time.process_time();fixed=read(Path(read(root/'stage402/plan.json')['fixed_plan']));ds=fixed['free_profile']['ds'];v=fixed['free_profile']['speed'];L=sum(ds);cum=[0.]
 def clock(s):
  acc=elapsed=0.
  for i,distance in enumerate(ds):
   part=min(max(s-acc,0),distance)
   if part>0:
    right=math.sqrt(v[i]**2+(v[i+1]**2-v[i]**2)*part/distance);elapsed+=2*part/(v[i]+right)
   acc+=distance
   if acc>=s:break
  return elapsed
 for i in range(1,11):cum.append(clock(L*i/10))
 x=read(d/'result.json');clocks=[]
 for i,b in enumerate(x['arc_bins']):clocks.append(dict(arc_fraction=b['arc_fraction'],ideal_profile_s=cum[i+1]-cum[i],prearc_attributed_actual_s=b['scored_time_s'],difference_attributed_s=b['scored_time_s']-(cum[i+1]-cum[i])))
 crossings=[dict(fraction=c['fraction'],actual_interval_s=c['interval_s'],ideal_profile_time_s=cum[i+1],actual_minus_ideal_interval_s=[t-cum[i+1] for t in c['interval_s']]) for i,c in enumerate(x['arc_crossing_intervals'])]
 rows=[json.loads(s) for s in (root/'stage402/P10_C/trace-private.jsonl').read_text().splitlines()];final=read(root/'stage402/P10_C/final-full-private.json');finish=final['wrapper']['finish_time_s'];groups=[]
 for name,pred in [('all',lambda r:True),('positive_clamp',lambda r:r['reference'].get('raw_accel',0)>fixed['model']['rear_traction_accel']),('target_gap_ge5',lambda r:r['reference'].get('r',r['pre']['speed'])-r['pre']['speed']>=5),('braking_below_target',lambda r:r['command'][2]>0 and r['pre']['speed']<r['reference'].get('r',r['pre']['speed']))]:
  selected=[r for r in rows if pred(r)];rr=[r for r in selected if 'command_accel' in r['reference']];weights=[max(0,min(r['post']['time'],finish)-r['pre']['time']) for r in rr];t=sum(weights)
  def avg(fn):return sum(w*fn(r) for r,w in zip(rr,weights))/t
  groups.append(dict(group=name,actions=len(rr),excluded_undefined_reference_actions=len(selected)-len(rr),scored_time_s=t,mean_requested_accel=avg(lambda r:r['reference']['command_accel']),mean_achieved_norm_accel=avg(lambda r:(r['post']['speed']-r['pre']['speed'])/(r['post']['time']-r['pre']['time'])),mean_requested_gas=avg(lambda r:r['command'][1]),max_rear_gas_request_lag=max(max(r['command'][1]-s['gas'],0) for r in rr for s in r['raw_tire_samples'] if s['wheel']>=2),time_with_requested_gas_lag= sum(w for r,w in zip(rr,weights) if any(s['wheel']>=2 and s['gas']<r['command'][1] for s in r['raw_tire_samples']))))
 result=dict(ideal_profile_clock_s=cum[-1],stored_clock_difference_s=cum[-1]-fixed['free_profile']['estimated_time_s'],official_actual_minus_ideal_s=x['official_lap_s']-cum[-1],bin_clock=clocks,cumulative_clock=crossings,actuator_groups=groups,new_native_actor_model_learning_SEALED=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start)
 assert abs(result['stored_clock_difference_s'])<1e-10;save(d/'supplement-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
