"""Missing-GT instrumentation of unchanged296 on three preselected known TRAIN."""
import datetime,fcntl,hashlib,json,random,sys,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
G=Path(__file__).resolve().parent.parent

def verify(root):
 d=root/'stage389';p=read(d/'instrumentation-plan.json');assert sha(d/'instrumentation-plan.json')==(d/'instrumentation-plan.sha256').read_text().strip();assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00'));assert not(d/'STOP').exists(),'Another instrumented case failed';return p

def charge(root,field):
 d=root/'stage389'
 with (d/'native-budget.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=read(d/'native-budget.json');limit=3 if field in ['resets','actor_resets'] else 6000;assert b[field]<limit;b[field]+=1;save(d/'native-budget.json',b)

def sensor(env):
 r=env.unwrapped;h=r.car.hull
 return dict(time=float(r.t),pos=list(h.position),vel=list(h.linearVelocity),angle=float(h.angle),yaw=float(h.angularVelocity),speed=float(np.hypot(*h.linearVelocity)),joint=[float(w.joint.angle) for w in r.car.wheels[:2]],road_contacts=[len(w.tiles) for w in r.car.wheels],wheel_gas=[float(w.gas) for w in r.car.wheels],wheel_brake=[float(w.brake) for w in r.car.wheels],wheel_omega=[float(w.omega) for w in r.car.wheels],visited=int(r.tile_visited_count),off_track_counter=int(env.off_track_counter))

def prepare(root):
 d=root/'stage389';assert not(d/'instrumentation-plan.json').exists();old=read(root/'stage306/plan.json');original=old['roads'][:6];assert original==['O0','O2','N0','N1','N2','N3'];missing=[k for k in original if not(root/'stage306/collection'/k/'full-source-captures-private.jsonl.gz').exists()];assert missing==['N0','N1','N2','N3'];selected=missing[:3]
 config=read(root/'stage377/plan.json')['config'];assert sha(config['archive_path'])==config['archive_sha256']=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937';assert sha(config['worker_path'])==config['worker_sha256'];assert read(root/'project-effective-budget-v407.json')['research_remaining']==35943
 sources=[Path(__file__),G/'retry/loss389_analyze.py',G/'retry/frozen_composite_runtime.py',G/'retry/qualify_pixel_package.py',G/'retry/pixel_sandbox_runtime.py',G/'retry/diagnose.py',G/'env_wrapper.py',G/'damage.py',root/'stage306/plan.json',root/'stage377/plan.json',root/'research-deadline-current.json',root/'project-effective-budget-v407.json',Path(config['archive_path']),Path(config['worker_path']),root/'stage88/pixel-read-sandbox']+list((G/'core').rglob('*.py'))+[Path(a['path']) for a in config['assets'].values()]
 for key in selected:sources += [root/'stage294/policies/g1p4'/key/name for name in ['job.json','result.json','trace-private.jsonl']]+[root/'stage375'/key/'reset-qualification.json']
 plan=dict(stage=389,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',selection='First3missing-full-GT cases in original306 TRAIN order; not ranked by lap/damage/failure or intervention outcome',original_order=original,missing_by_field_inventory=missing,selected=selected,cases={k:old['cases'][k] for k in selected},config=config,sandbox_path=str(root/'stage88/pixel-read-sandbox'),observer_rng_seed=375,per_case_cap=2000,total_native_cap=6000,max_resets=3,max_parallel_cases=2,research_before=35943,research_after_worst_case=29943,final_reserved_actions=84000,final_reserve_used=0,new_policy=False,new_training=False,new_sweep=False,qualification='Unchanged296ZIP/modules/normalmemory/fullreturnedcontrols; observer375 matches prior375 initialmetadata, old294 action/feature/collision/damage streams checked if corresponding rows available; GT supervisor only',stops='Officialfinish/retirement first; else native2000/cap6000/approvalend ->censor, notDNF. Firstsource/legality/reset/actionintegrity/technicalfailure stops remaining new cases withoutretry. Actualcost only; no automaticreplacement.',metrics='Per-action pre/post source time, hull pose/velocity/yaw, joints/contacts/appliedwheelpedals, tracker/path/target/fullcommands, visited/damage/collision/finish. First static fulltrack/roadpolygons/obstacles; no force/solvercounterfactuals.',forbidden='372failure data,SEALED,sourcephysics forecasts,parameter draws',source_hashes={str(f):sha(f) for f in sources},protected_hashes={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']})
 save(d/'instrumentation-plan.json',plan);f=d/'instrumentation-plan.sha256';f.write_text(sha(d/'instrumentation-plan.json')+'\n');f.chmod(0o600);save(d/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=6000));(d/'replay').mkdir(mode=0o700);print('389registeredN0,N1,N2 bymissing-field order; unchanged296,cap6000/from35943,reserve84000untouched',flush=True)

def episode(root,key):
 from retry.frozen_composite_runtime import prepare as actor_prepare,validate_response
 from retry.diagnose import make_env
 from retry.pedal331_run import physical,rng
 d=root/'stage389';p=verify(root);assert key in p['selected'];f=d/'replay'/key;assert not f.exists();f.mkdir(mode=0o700);save(f/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));config=p['config'];old=read(root/'stage294/policies/g1p4'/key/'result.json');oldrows=[json.loads(s) for s in (root/'stage294/policies/g1p4'/key/'trace-private.jsonl').read_text().splitlines()];reference=read(root/'stage375'/key/'reset-qualification.json');worker=env=journal=None;steps=ticks=0;reset=0;actorcpu=0.;error=None;ended=truncated=complete=False;info={};start_t=None;rows=[];latencies=[];resetqualified=False;baseline_matches=0;reaping=None
 start,cpu=time.perf_counter(),time.process_time();random.seed(p['observer_rng_seed']);np.random.seed(p['observer_rng_seed'])
 try:
  for path,h in p['source_hashes'].items():assert sha(path)==h,path
  worker=actor_prepare(config,f/'cpu',p['sandbox_path']);save(f/'ready-private.json',worker.ready);env=make_env();case=p['cases'][key];charge(root,'resets');obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;start_t=float(raw.t);reset=round(raw.t*50)
  image=hashlib.sha256(obs.tobytes()).hexdigest();geom=hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest();obhash=hashlib.sha256(np.asarray([[*map(float,o.position),float(o.fixtures[0].shape.radius)] for o in raw.obstacles],dtype='<f8').tobytes()).hexdigest();assert image==reference['initial_observation_sha256'] and geom==reference['geometry_sha256'] and obhash==reference['physical_obstacles_sha256'];save(f/'initial-scene-private.json',physical(env));save(f/'initial-RNG-private.json',rng(env));save(f/'geometry-private.json',dict(line=np.asarray(raw.track)[:,2:4].tolist(),road_polygons=[[[float(v[0]),float(v[1])] for v in [body.transform*z for z in body.fixtures[0].shape.vertices]] for body in raw.road],obstacles=[[float(o.position[0]),float(o.position[1]),float(o.fixtures[0].shape.radius)] for o in raw.obstacles]))
  charge(root,'actor_resets');r,ms=worker.call('reset',obs);validate_response(r,config,obs,'reset');assert r['state']['previous_steer']==0 and r['state']['hazards']==[];resetqualified=True;save(f/'reset-qualification.json',dict(passed=True,original296=True,initial_pixel_geometry_obstacle_hashes_match375=True))
  journal=(f/'trace-private.jsonl').open('x');(f/'trace-private.jsonl').chmod(0o600)
  for i in range(2000):
   verify(root);pre=sensor(env);charge(root,'actor_act_calls');r,ms=worker.call('act',obs);a=validate_response(r,config,obs,'act');assert r['delta_audit'] is None
   if i<len(oldrows):assert a.tolist()==oldrows[i]['action'] and r['features']==oldrows[i]['features'],('old296action/features',i);baseline_matches+=1
   charge(root,'actor_commit_calls');ack,_=worker.call('commit',a);assert ack['memory']==ack['nominal_memory']==r['state']['previous_steer'];actorcpu=ack['actor_cumulative_CPU_s'];charge(root,'actions');steps+=1;before=raw.t;obs,_,ended,truncated,info=env.step(a);rt=round((raw.t-before)*50);ticks+=rt;post=sensor(env);complete=raw.finish_time_s is not None
   row=dict(step=steps,pre=pre,post=post,action=a.tolist(),features=r['features'],memory=ack['memory'],pixel_path=r['pixel_path'],tracker=r['tracker_record'],collision=bool(info['collision']),damage=float(env.damage.damage),raw_ticks=rt,completed=complete,terminated=bool(ended),truncated=bool(truncated),finish_time_s=raw.finish_time_s,retire_reason=info.get('retire_reason'),actor_IPC_ms=ms);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush();rows.append(row);latencies.append(ms)
   if i<len(oldrows):assert row['collision']==oldrows[i]['collision'] and row['damage']==oldrows[i]['damage'],('old296collision/damage',i)
   if ended or truncated:break
 except BaseException as exc:
  error=type(exc).__name__+': '+str(exc);save(f/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()));(d/'STOP').write_text(error)
 finally:
  if journal:journal.close()
  if worker:reaping=worker.close()
  if env:env.close()
 result=dict(case=key,native_actions=steps,native_cap=2000,reset_qualified=resetqualified,completed=bool(complete),actual_DNF=bool(ended and not complete),censored=bool(error or not complete and not ended),technical_error=error,terminated=bool(ended),truncated=bool(truncated),retire_reason=info.get('retire_reason'),lap_ms=round((rows[-1]['finish_time_s']-start_t)*1000) if complete else None,damage=rows[-1]['damage'] if rows else None,visited=rows[-1]['post']['visited'] if rows else None,raw_step_ticks=ticks,raw_reset_ticks=reset,baseline_rows_exact=baseline_matches,old_baseline_lap_ms=old['lap_ms'],old_baseline_native=old['native_actions'],wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,max_actor_IPC_ms=max(latencies) if latencies else None,reaping=reaping,archive_sha256=config['archive_sha256'],unconfirmed_charged_native=steps-len(rows))
 if not error:assert result['lap_ms']==old['lap_ms'] and result['native_actions']==old['native_actions'] and result['damage']==old['damage']
 save(f/'result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
 root=Path(sys.argv[1]).resolve()
 if len(sys.argv)==2:prepare(root)
 else:episode(root,sys.argv[2])
