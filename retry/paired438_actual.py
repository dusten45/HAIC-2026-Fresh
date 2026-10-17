"""Exactly two fresh actual arms; future436 commands are never selection inputs."""
import copy,json,random,time,traceback
from dataclasses import asdict
import numpy as np
from retry.paired417_common import ActualC,Trace,metrics,shapecheck,canonical_projection,ModelFailure,SafetyStop,Ineligible,read,save
from retry.planner419 import GoalLedger,H
from retry.fork394_run import complete_state
from retry.loss389_replay import sensor
from retry.pilot398_run import safety_flags,raw_capture_pairs
from retry.headroom413_run import row_fidelity
from retry.actual437_boundary import ActualHistory437,Dispatch437
from retry.paired438_query import Query438
from retry.receipt421_io import save_receipt

def actual_pairs(root,meter,fixed,pace):
 from retry.diagnose import make_env
 d=root/'stage438';p=read(d/'plan.json');line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);prefix=[json.loads(t) for t in (root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()][:118];source_prefix=read(root/'stage417/source-prefix-private.json');results=[];meter.begin_actual()
 try:
  for arm,limit in [('C0',80),('P',100)]:
   folder=d/('actual_'+arm);folder.mkdir(mode=0o700);env=ctrl=obs=trace=journal=history=None;rows=[];checks=[];commits=[];queries=[];status='STARTED';error=None;stage='reset';planner_used=0;progress=previous=goal=deadline=None;prefixexact=0;rawticks=reset_ticks=0;official_finish=lap_ms=None;start_time=None;ac0=meter.nb['actions'];mt0=meter.b['ticks'];ww0=meter.b['worlds'];cpu=time.process_time();wall=time.perf_counter();mc0,mw0=meter.modeltime();query=Query438(root,meter,fixed,pace)
   try:
    random.seed(394);np.random.seed(394);env=make_env();meter.charge('reset',arm);obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});ctrl=ActualC(env,fixed,pace);initial=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',initial);start_time=float(env.unwrapped.t);reset_ticks=round(start_time*50)
    if initial!=read(root/'stage423/actual_C0/initial-private.json'):raise ModelFailure('actual_initial_state_RNG_pixels_mismatch')
    contacts=set(tuple(x) for x in initial['physical']['touching_obstacle_contacts']);trace=Trace(lambda:env.unwrapped.t);dispatcher=Dispatch437(env,'ACTUAL438_'+arm);journal=(folder/'trace-private.jsonl').open('x')
    for step in range(1,119+limit):
     meter.guard();stage='prefix' if step<=118 else 'suffix';before=copy.deepcopy(ctrl.memory());nominal=ctrl.act(env);pre=sensor(env);proj=canonical_projection(line,pre['pos'],pre['vel'],ctrl.phase());why=safety_flags(pre,proj,float(env.damage.damage),0.)
     if why:raise SafetyStop('actual_pre:'+','.join(why))
     if progress is None:progress=prefix[0]['progress_before'];previous=proj['arc']
     if goal is None or progress>=goal:goal=progress+3.24;deadline=step-1+13
     frame=pending=record=None
     if step<=118:
      ref=prefix[step-1]
      if pre!=ref['pre'] or nominal.tolist()!=ref['nominal'] or before!=ref['memory_before']:raise ModelFailure('prefix_pre_nominal_memory:'+str(step))
      command=np.asarray(ref['command'],np.float32)
     else:
      if step==119:
       ledger=GoalLedger(progress,goal,H-(deadline-(step-1)),round(pre['time']*50));fork=complete_state(env,obs,dict(before=before,after=ctrl.memory(),nominal=nominal.tolist()));save(folder/'fork-private.json',fork)
       if fork!=read(root/'stage423/actual_C0/fork-private.json'):raise ModelFailure('pre119_full_root_state_memory_clock_RNG')
       if arm=='P' and fork!=read(d/'actual_C0/fork-private.json'):raise ModelFailure('fresh_C0_P_root_mismatch')
       history=ActualHistory437(env,obs,ctrl,ledger,fixed,dispatcher,arm)
      frame,record,pending=query.query(history,before,nominal,arm,step-118,planner_used);queries.append(record);planner_used+=int(record['planner_used']);command=np.asarray(frame['command'],np.float32)
     save_receipt(folder/('step'+str(step)+'-before-native-private.json'),dict(step=step,full=complete_state(env,obs,ctrl.memory()),memory_before=before,nominal=nominal.tolist(),command=command.tolist(),ledger=None if history is None else asdict(history.ledger),model_prediction_does_not_commit=True,actual_calls_before=meter.nb['actions']))
     meter.charge('action',arm);out,ticket=dispatcher.call(command,trace);obs,_,ended,truncated,info=out;post=sensor(env);rt=round((post['time']-pre['time'])*50);rawticks+=rt;damage=float(env.damage.damage);q=dict(position=post['pos'],velocity=post['vel'],angle=post['angle'],angular_velocity=post['yaw'],speed_m_s=post['speed'],damage=damage,collision=bool(info['collision']),wheel_road_contacts=sum(n>0 for n in post['road_contacts']));postproj,why=metrics(q,trace.rows,trace.hulls,line,ctrl.phase())
     if set(tuple(z) for z in raw_capture_pairs(env))-contacts:why.append('new_obstacle_contact')
     nextprogress=progress+(postproj['arc']-previous+L/2)%L-L/2;hit=nextprogress>=goal or env.unwrapped.finish_time_s is not None
     if step>=deadline and not hit:why.append('actual_progress_deadline')
     row=dict(step=step,pre=pre,post=post,nominal=nominal.tolist(),command=command.tolist(),memory_before=before,nominal_memory_after=copy.deepcopy(ctrl.memory()),raw_ticks=rt,raw_tire_samples=copy.deepcopy(trace.rows),raw_hull=copy.deepcopy(trace.hulls),post_projection=postproj,collision=bool(info['collision']),damage=damage,completed=env.unwrapped.finish_time_s is not None,finish_time_s=env.unwrapped.finish_time_s,ended=bool(ended),truncated=bool(truncated),safety=why,progress_before=progress,progress_after=nextprogress,goal_before=goal,deadline_before=deadline,goal_hit_actual_step=hit,current_query=record)
     rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush();dispatcher.check(ticket,row)
     if step<=118:
      ref=prefix[step-1]
      for key in ['pre','post','nominal','command','memory_before','nominal_memory_after','raw_ticks','raw_tire_samples','raw_hull','collision','damage','completed','finish_time_s','ended','truncated']:
       if row[key]!=ref[key]:raise ModelFailure('prefix_exact_native_row:'+str(step)+':'+key)
      z=row_fidelity(source_prefix[step-1],row);checks.append(z)
      if not z['passed'] or z['wheel']['clipped_flag_mismatches']:raise ModelFailure('prefix_source_fidelity')
      prefixexact+=1;dispatcher.consume(ticket)
     else:
      z=shapecheck(frame,row);checks.append(z)
      if not z['passed'] or z['wheel']['clipped_flag_mismatches']:raise ModelFailure('selected_first_body_wheel_raw_hull_phase_clip:'+str(step))
      if frame['memory_before']!=before or frame['memory_after']!=ctrl.memory():raise ModelFailure('selected_first_memory_exact:'+str(step))
      commitment=history.commit(ticket,row,obs,frame,pending);commits.append(dict(step=step,**commitment));save_receipt(folder/('step'+str(step)+'-actual-commit-private.json'),dict(proof=commitment,actual_ledger=asdict(history.ledger),actual_tracker=dict(env.unwrapped.finish_line_tracker.__dict__),selected_first_check=z));progress=history.ledger.progress_m;goal=history.ledger.goal_m;deadline=step+H-history.ledger.age_actions
     if why:raise SafetyStop('actual_post:'+','.join(why))
     progress=nextprogress;previous=postproj['arc']
     if step>118:print(json.dumps(dict(stage=438,arm=arm,suffix=step-118,planner=bool(record['planner_used']),recipe=record['selected_recipe'],actual_actions=meter.nb['actions'],model_ticks=meter.b['ticks'],worlds=meter.b['worlds'])),flush=True)
     if row['completed']:
      if history is None or not history.ledger.done:raise ModelFailure('native_finish_without_actual_ledger_commit')
      ctrl.done(env);official_finish=float(env.unwrapped.finish_time_s);lap_ms=round((official_finish-start_time)*1000);status='COMPLETED_SAFE_OFFICIAL';break
     if ended or truncated:raise Ineligible('actual_nonfinish_terminal_no_time_estimate')
    else:status='ACTUAL_ACTION_CAP_CENSORED'
   except BaseException as e:status='CENSORED_STOP';error=type(e).__name__+': '+str(e);save(folder/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc()))
   finally:
    if trace:trace.disable()
    if journal:journal.close()
    if history:save_receipt(folder/'observed-history-private.json',dict(root=history.root,initial_ledger=asdict(history.initial),posts=history.posts,actions=history.actions,actual_commits=history.actual_commits,actual_ledger=asdict(history.ledger)))
    if env:
     try:save(folder/'final-private.json',complete_state(env,obs,ctrl.memory() if ctrl else {}))
     finally:env.close()
   mc,mw=meter.modeltime();tires=[t for row in rows for t in row['raw_tire_samples']];suffix=rows[118:];ft=next((x for x in suffix if x['completed']),None);event_bracket=None
   if ft:
    # An event at an earlier raw tick is retained separately from confirmation.
    root_time=suffix[0]['pre']['time'];event_tick=round((ft['finish_time_s']-root_time)*50);event_bracket=[event_tick-1,event_tick]
   rr=dict(arm=arm,status=status,error=error,prefix_exact_rows=prefixexact,suffix_rows=len(suffix),confirmed_rows=len(rows),native_actions=meter.nb['actions']-ac0,unconfirmed_native_actions=meter.nb['actions']-ac0-len(rows),reset_ticks=reset_ticks,raw_step_ticks=rawticks,planner_decisions=planner_used,guardian_decisions=len(queries)-planner_used,completed=status=='COMPLETED_SAFE_OFFICIAL',lap_ms=lap_ms,official_event_time_s=official_finish,confirmation_time_s=None if ft is None else ft['post']['time'],suffix_event_rawtick_bracket=event_bracket,actual_ledger=None if history is None else asdict(history.ledger),actual_commits=len(commits),pending_routes=sum(r['route']=='REGISTERED_PENDING_GUARDIAN_ONLY' for r in queries),damage=rows[-1]['damage'] if rows else None,max_post_path_error_m=max((r['post_projection']['path_error_m'] for r in rows),default=None),max_force_ratio=max((t['force_ratio'] for t in tires),default=None),clipped_wheel_samples=sum(t['clipped'] for t in tires),wheel_samples=len(tires),suffix_max_force_ratio=max((t['force_ratio'] for r in suffix for t in r['raw_tire_samples']),default=None),selected_first_fidelity_passed=len(checks)==len(rows) and all(z['passed'] for z in checks),memory_and_ledger_exact_commits=len(commits),exclusive_actual_CPU_s=time.process_time()-cpu-(mc-mc0),exclusive_actual_wall_s=time.perf_counter()-wall-(mw-mw0),model_ticks=meter.b['ticks']-mt0,model_worlds=meter.b['worlds']-ww0,new_state_force_qualification='Only observed transitions in this arm; no qualification beyond this range.',new_pixel_or_generalization_qualification=False)
   save(folder/'fidelity-checks.json',checks);save(folder/'result.json',rr);results.append(rr);save(d/'actual-results.json',results);print(json.dumps(dict(stage=438,arm=arm,status=status,error=error,actions=len(rows),lap_ms=lap_ms)),flush=True)
   if status!='COMPLETED_SAFE_OFFICIAL':break
 finally:meter.end_actual();save(d/'actual-results.json',results);save(d/'query-records-private.json',meter.queries)
 return results
