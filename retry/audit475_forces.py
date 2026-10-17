"""Saved arithmetic only: no body integration, controller call or future action."""
import datetime,hashlib,json,math,sys,time
from pathlib import Path
from retry.audit474_traces import NoPhysics,RUNS
G=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,d):
 with Path(p).open('x') as f:json.dump(d,f,indent=2,allow_nan=False);f.write('\n')
 Path(p).chmod(0o600)
def prepare(root):
 p=read(root/'stage474-plan-durable-private.json');d=Path('/tmp/haic-retry-stage475-private');assert not d.exists();assert not(root/'stage475').exists()
 sources=dict(p['sources']);sources.update({str(G/'retry/audit475_forces.py'):sha(G/'retry/audit475_forces.py')})
 extra=[G/'env_wrapper.py',G/'damage.py',root/'stage473/world42-before-first-step-private.json',root/'stage473/world43-before-first-step-private.json']
 for f in extra:sources[str(f)]=sha(f)
 plan=dict(stage=475,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),mode='SAVED_ARITHMETIC_ONLY',sources=sources,protected=p['protected'],original408_preserve=p['original408_preserve'],deadline_utc=p['deadline_utc'],new_physics=0,new_native=0,new_reset=0,new_actor=0,raw_allowance_bytes=16*1024**2,CPU_cap_s=30,wall_cap_s=60,predeclared_gates=['no physics imports','hashes unchanged','exact matches reported separately from errors; no tolerance promoted to exact','missing wheel state blocks independent geometry proof','no allocator execution or physics promotion'],stop='missing source/hash mismatch/nonfinite/schema inconsistency stops; numerical differences reported without tuning',scope='all saved raw plus first raw per wrapper, root snapshots; no new trajectory or counterfactual action dispatch')
 d.mkdir(mode=0o700);(root/'stage475').symlink_to(d,target_is_directory=True);put(d/'plan.json',plan);put(root/'stage475-plan-durable-private.json',plan);print('registered',sha(d/'plan.json'))
def run(root):
 guard=NoPhysics();sys.meta_path.insert(0,guard)
 import numpy as np
 d=root/'stage475';p=read(d/'plan.json');cpu=time.process_time();wall=time.perf_counter()
 for group in ['sources','protected','original408_preserve']:
  for f,h in p[group].items():assert sha(f)==h,f
 result={};records=[]
 for label,(rel,observer) in RUNS.items():
  model=observer is not None;payload=read(root/rel) if model else None;rows=payload['rows'] if model else [json.loads(s) for s in (root/rel).read_text().splitlines() if s]
  state=read(root/('stage473/world43-before-first-step-private.json' if label=='473_P4' else 'stage473/world42-before-first-step-private.json'))['model_root']['physical'] if model else read(root/rel.replace('trace-private.jsonl','initial-private.json'))['physical']
  assert state['damage']==0
  prev=[dict(omega=w['dynamics']['omega'],gas=w['dynamics']['gas']) for w in state['wheels']]
  errors={k:[] for k in ['gas','brake','omega','long_force','lat_force','force_ratio','slip']};first={k:[] for k in errors};branches={};empty=dict(lateral_alone_raw_states=0,pedal_invariant_front_violation_raw_states=0,lateral_alone_wrapper_firsts=0,pedal_invariant_front_violation_wrapper_firsts=0);command_f32=True;totalraw=0;exactroot={}
  for wi,row in enumerate(rows,1):
   command=np.asarray(row['command'],dtype=np.float64 if model else np.float32);command_f32 &= all(float(np.float32(x))==float(x) for x in command)
   tires=row['tires'] if model else row['raw_tire_samples'];n=len(row['raw_hull'])
   assert row['predicted']['damage']==0 if model else row['damage']==0
   for tick in range(1,n+1):
    totalraw+=1;ts=[t for t in tires if t['raw_tick']==tick];assert len(ts)==4
    latbad=any(abs(t['raw_lat_N'])>t['friction_limit'] for t in ts)
    # On gas-active branch front gas stays0 and brake stays0: q cannot change front demand.
    frontbad=command[1]>0 and command[2]==0 and any(t['wheel']<2 and t['clipped'] for t in ts)
    empty['lateral_alone_raw_states']+=latbad;empty['pedal_invariant_front_violation_raw_states']+=bool(frontbad)
    if tick==1:empty['lateral_alone_wrapper_firsts']+=latbad;empty['pedal_invariant_front_violation_wrapper_firsts']+=bool(frontbad)
    for t in ts:
     j=t['wheel'];old=prev[j];gas=old['gas']
     if j>=2:
      diff=np.clip(command[1],0,1)-gas
      if diff>0.1:diff=0.1
      gas+=diff
     brake=command[2];omega0=old['omega'];omega=omega0+.02*(100000000*.02*.02)*gas/(4000*.02*.02)/(abs(omega0)+5.)
     if brake>=.9:omega=0;branch='lock'
     elif brake>0:
      val=15*brake
      if abs(val)>abs(omega):val=abs(omega);branch='zero_clamp'
      else:branch='brake_linear'
      omega+=-np.sign(omega)*val
     else:branch='no_brake'
     branches[branch]=branches.get(branch,0)+1
     # Stored vf/vs are inputs, not independently regenerated wheel kinematics.
     vf=t['forward_speed_m_s'];vs=t['lateral_slip_m_s'];vr=omega*.54;long=(-vf+vr)*(205000*.02*.02);lat=-vs*(205000*.02*.02);force=np.sqrt(np.square(long)+np.square(lat));ratio=force/t['friction_limit']
     es=dict(gas=abs(float(gas)-t['gas']),brake=abs(float(brake)-t['brake']),omega=abs(float(omega)-t['omega']),long_force=abs(float(long)-t['raw_long_N']),lat_force=abs(float(lat)-t['raw_lat_N']),force_ratio=abs(float(ratio)-t['force_ratio']),slip=abs(float(vr-vf)-t['longitudinal_slip_m_s']))
     for k,v in es.items():errors[k].append(v);first[k].extend([v] if tick==1 else [])
     # Anchor next omega at observed preclip omega and source reaction arithmetic;
     # this is a saved local transition identity, not integrated wheel dynamics.
     obsforce=np.sqrt(np.square(t['raw_long_N'])+np.square(t['raw_lat_N']));ff=t['raw_long_N']
     if abs(obsforce)>t['friction_limit']:ff/=obsforce;ff*=t['friction_limit']
     prev[j]=dict(omega=t['omega']-.02*ff*.54/(4000*.02*.02),gas=gas)
     q=dict(run=label,wrapper=wi,raw_tick=tick,wheel=j,branch=branch,errors=es,omega_before_source='full_root_snapshot' if wi==1 and tick==1 else 'previous_observed_omega_minus_reconstructed_reaction',inputs_vf_vs_limit='saved telemetry; independent geometry not available except root',gas_dtype=type(gas).__name__)
     records.append(q)
  def summarize(v):return dict(n=len(v),exact=sum(x==0 for x in v),max_abs_error=max(v,default=0))
  result[label]=dict(wrappers=len(rows),raw_states=totalraw,wheel_samples=len(errors['gas']),all_commands_exact_float32=bool(command_f32),action_transport_dtype='float64 model' if model else 'float32 native',all_raw={k:summarize(v) for k,v in errors.items()},wrapper_first_raw={k:summarize(v) for k,v in first.items()},branches=branches,necessary_empty_conditions=empty)
  assert time.process_time()-cpu<30 and time.perf_counter()-wall<60
 for group in ['sources','protected','original408_preserve']:
  for f,h in p[group].items():assert sha(f)==h,f
 with (d/'checks-private.jsonl').open('x') as f:
  for q in records:f.write(json.dumps(q,allow_nan=False)+'\n')
 out=dict(stage=475,status='SAVED_RECONSTRUCTION_COMPLETE_NO_INTEGRATION',plan_sha256=sha(d/'plan.json'),numpy_version=np.__version__,runs=result,new_physics=0,new_native=0,new_resets=0,new_actor_calls=0,import_guard_attempts=guard.attempts,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,sources_and_protected_preserved=True,limits=['vf/vs/friction_limit are stored inputs, not independent before-state reconstruction','all later omega starts use preceding observed omega and arithmetic reaction; no solver or trajectory regenerated','native original action scalar dtype inferred from source and float32 transport; recorded agreement cannot prove every historical dtype','all runs damage0; no damaged engine/grip certification','no allocator search implemented; no maximality or hold safety certification'])
 put(d/'result.json',out);put(G/'retry/audit475_result.json',out);print(json.dumps(out))
if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
