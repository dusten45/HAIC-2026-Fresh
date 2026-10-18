"""Recover serialization-only report loss; perform ONLY unexecuted final replay.

No optimization, FD, LP, proposal retry, new window or accepted-step change.
The original failed source and all failed raw trajectories remain untouched.
"""
import datetime,json,math,signal,time,traceback
from pathlib import Path
import numpy as np
import retry.sequential560_model as model
import retry.period556_model as engine

G=model.G;D=model.D;rd,sha=model.rd,model.sha
def normal(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,dict):return {k:normal(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [normal(v) for v in x]
 return x
base_save=engine.save
def save(p,x,overwrite=False):return base_save(p,normal(x),overwrite)
# Isolated adapter, not a change to the frozen scientific model or decisions.
model.save=save;engine.save=save

def run():
 original=rd(G/'retry/sequential560_contract.json');failure=rd(D/'failure-private.json');segment=rd(D/'segment-private.json');baseline=rd(D/'baseline-private.json');assert failure['error']=='TypeError:Object of type int64 is not JSON serializable';assert failure['cost']['trial_rollouts']==3 and failure['cost']['FD_rollouts']==40
 trials=[rd(D/f'trial-00-{j:02d}-private.json') for j in range(3)];assert all(not t['physical_safe'] and not t['feasible'] for t in trials);assert len(list(D.glob('incumbent-*-private.json')))==1
 c=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Serialization recovery from saved results plus ONLY the original unexecuted final baseline-incumbent132raw replay. Three rejected trials already trigger original stop. No scientific rerun or new direction/LP/step.',original_contract_sha256=sha(G/'retry/sequential560_contract.json'),original_failure_sha256=sha(D/'failure-private.json'),caps=dict(additional_model_ticks=132,additional_explicit_wheel_forces=528,additional_geometry_checks=133,CPU_s=10,wall_s=20),accounting='Main CPU/perf-wall floats were lost before JSON serialization. Do NOT invent aggregate measured CPU or assert aggregateCPU600 audit. Retain original hard timer bound600 and approximate registration-to-failure file wall separately. Recovery CPU/wall measured directly.',source_sha256={p:sha(G/p) for p in ['retry/sequential560_recover.py',*model.SOURCES]})
 save(G/'retry/sequential560_recovery_contract.json',c);save(D/'recovery-STARTED.json',dict(contract_sha256=sha(G/'retry/sequential560_recovery_contract.json')))
 cpu,wall=time.process_time(),time.perf_counter();study=model.Study.__new__(model.Study);study.static,study.paths,data=map(rd,model.INPUTS);study.path=study.paths['candidate'];study.before=segment['initial'];study.initial=engine.load_root(dict(study.before,roads=study.static['root']['roads']));study.history=segment['history'];trace=data['trace'];j=next(i for i,x in enumerate(trace) if x['index']==segment['entry_action'] and x['raw']==1);study.progress=trace[j-1]['progress'];study.base_actions=[np.array(a,np.float32) for a in segment['commands']];study.gates=[dict(g,baseline_vector=np.array(g['baseline_vector']),tolerance=np.array(g['tolerance'])) for g in segment['gates']];study.counter=[failure['model_ticks']];study.cost=dict(failure['cost']);study.index=engine.bounds(study.initial.roads);study.edge=engine.boundary_index(study.static['boundary']);study.current='recovery_final_only';study.incumbent={'label':'baseline'};study.evaluation_count=study.cost['evaluations']
 def guard(*_):
  if study.counter[0]>=failure['model_ticks']+132 or study.cost['explicit_wheel_force_evaluations']+4>failure['cost']['explicit_wheel_force_evaluations']+528 or study.cost['geometry_checks']>=failure['cost']['geometry_checks']+133:raise RuntimeError('RECOVERY_WORK_CAP')
  if time.process_time()-cpu>=10 or time.perf_counter()-wall>=20:raise RuntimeError('RECOVERY_TIME_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(original['deadline_utc']):raise RuntimeError('DEADLINE')
 study.guard=guard;signal.signal(signal.SIGPROF,guard);signal.setitimer(signal.ITIMER_PROF,10);signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,20)
 final=None;error=None
 try:
  final=study.evaluate(np.array(baseline['x']),'final');assert final['feasible']
  assert all(model.canonical(engine.short(s))==r['root_without_roads'] for s,r in zip(final['states'][1:],baseline['rows']))
 except BaseException as e:
  error=type(e).__name__+':'+str(e);save(D/'recovery-error-private.json',dict(error=error,traceback=traceback.format_exc(),cost=study.cost,model_ticks=study.counter[0]))
 finally:signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 recovery_cost=dict(model_ticks=study.counter[0]-failure['model_ticks'],explicit_wheel_force_evaluations=study.cost['explicit_wheel_force_evaluations']-failure['cost']['explicit_wheel_force_evaluations'],geometry_checks=study.cost['geometry_checks']-failure['cost']['geometry_checks'],CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 fd=[rd(D/f'FD-00-{i:02d}-private.json') for i in range(40)];x=np.array(baseline['x']);steps=[f['x'][i]-x[i] for i,f in enumerate(fd)];times=lambda v:np.array([z['time'] for z in v['crossings']]);T=np.array([(times(f)-times(baseline))/steps[i] for i,f in enumerate(fd)]).T;records=[]
 def active(v):
  return {name:dict(min_slack=float(min(g for g,n in zip(v['g'],v['labels']) if n==name)),near_or_violated=int(sum(g<=1e-5 for g,n in zip(v['g'],v['labels']) if n==name))) for name in sorted(set(v['labels']))}
 def branch(a,b):
  aa=np.array([f['clipped'] for r in a['rows'] for f in r['forces']]);bb=np.array([f['clipped'] for r in b['rows'] for f in r['forces']]);u=np.array(a['x'])[1::2];v=np.array(b['x'])[1::2]
  return dict(contact_raw_changes=int(sum(r['root_without_roads']['current_contacts']!=s['root_without_roads']['current_contacts'] for r,s in zip(a['rows'],b['rows']))),new_clipped_samples=int(sum(bb&~aa)),freed_clipped_samples=int(sum(aa&~bb)),pedal_mode_changes=int(sum(np.sign(u)!=np.sign(v))),brake_lock_changes=int(sum((u<=-.9)!=(v<=-.9))))
 for i,v in enumerate(trials):
  predicted=-(T@(np.array(v['x'])-x));actual=times(baseline)-times(v);ratio=float(np.mean(actual)/np.mean(predicted));err=float(max(abs(actual-predicted)));agree=.25<=ratio<=2 and err<=max(.0005,.5*max(abs(predicted)))
  records.append(dict(trial=i+1,radius=2.**(-i),label=f'trial-00-{i:02d}',predicted_gain_ms=(1000*predicted).tolist(),actual_gain_ms=(1000*actual).tolist(),prediction_max_error_ms=1000*err,actual_predicted_ratio=ratio,agreement=bool(agree),physical_safe=v['physical_safe'],source_feasible=v['feasible'],accepted=False,branch_changes=branch(baseline,v),active_constraints=active(v),incumbent_preserved_on_reject=True))
 save(D/'recovered-direction-00-private.json',dict(direction=1,FD_steps=steps,trials=records,from_saved_no_new_solve=True))
 main_wall_est=(D/'failure-private.json').stat().st_mtime-datetime.datetime.fromisoformat(original['registered_utc']).timestamp()
 out=dict(completed=error is None,scientific_stop_reason='THREE_REJECTED_TRIALS',execution_issue='Original reporting failed serializing NumPy int64 boundary counts; scientific decisions restored from saved records without rerun.',recovery_error=error,exact_feasible_initialization=True,accepted_count=0,direction_count=1,trials=records,incumbent_label='baseline',incumbent_preserved=True,final_fresh_replay_exact=error is None,final_feasible=bool(final and final['feasible']),baseline_times_s=times(baseline).tolist(),final_times_s=final['times'].tolist() if final else None,cumulative_gain_ms=(1000*(times(baseline)-final['times'])).tolist() if final else None,baseline_brackets=[g['raw_bracket'] for g in baseline['crossings']],final_brackets=[g['raw_bracket'] for g in final['crossings']] if final else None,final_state_differences=final['gate_world_state_differences'] if final else None,final_active_constraints=active(rd(D/'final-private.json')) if final else None,final_stats=rd(D/'final-private.json')['stats'] if final else None,cost=dict(study.cost,model_ticks=study.counter[0],internal_wheel_force_evaluations=4*study.counter[0],main_measured_CPU_s=None,main_measured_perf_wall_s=None,main_registration_to_failure_file_wall_estimate_s=main_wall_est,main_CPU_hard_timer_s=600,aggregate_CPU600_independently_verified=False,recovery=recovery_cost),new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_lap_gain_observation=True)
 save(G/'retry/sequential560_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':run()
