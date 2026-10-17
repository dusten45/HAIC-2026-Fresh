"""One actual C0/P pair, each history118 plus13; no full-lap continuation."""
import copy,json,math,random,time,traceback
from dataclasses import asdict
import numpy as np
from retry.paired417_common import *
from retry.calibrate422_model import query
from retry.planner419 import GoalLedger,ActualObservation,H
from retry.fork394_run import complete_state
from retry.loss389_replay import sensor
from retry.pilot398_run import safety_flags,raw_capture_pairs
from retry.terminal409_contract import validate
def actual_pairs(root,meter,fixed,pace,source,prefix):
 from retry.diagnose import make_env
 d=root/'stage422';p=read(d/'plan.json');line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);old=[json.loads(t) for t in (root/'stage411/policy_C/trace-private.jsonl').read_text().splitlines()];results=[];meter.begin_actual()
 try:
  for arm in ['C0','P']:
   folder=d/('actual_'+arm);folder.mkdir(mode=0o700);env=obs=tr=journal=None;rows=[];checks=[];source_fidelity=[];queries=[];recipe_aligned=True;laststage='reset';error=None;status='STARTED';progress=previous=goal=deadline=None;prefixexact=0;rawstep=reset_ticks=0;start_arc=None;native_before=meter.nb['actions'];model_before=meter.mb['ticks'];world_before=meter.mb['worlds'];neutral_steps=[];changed_commands=[];witnesses=[];segment_checks=[];divergences=[];decisions=[];ledger=None;epicpu=time.process_time();epiwall=time.perf_counter();modelc0,modelw0=meter.modeltime()
   try:
    random.seed(394);np.random.seed(394);env=make_env();meter.charge('reset',arm);obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});ctrl=ActualC(env,fixed,pace);ini=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',ini)
    if ini!=read(root/'stage418/actual_A/initial-private.json'):raise ModelFailure('actual_initial_full_RNG_pixels')
    pairs=set(tuple(z) for z in ini['physical']['touching_obstacle_contacts']);reset_ticks=round(env.unwrapped.t*50);tr=Trace(lambda:env.unwrapped.t);journal=(folder/'trace-private.jsonl').open('x')
    for step in range(1,132):
     meter.guard();laststage='prefix' if step<=118 else 'suffix';before=ctrl.memory();nominal=ctrl.act(env);pre=sensor(env);proj=canonical_projection(line,pre['pos'],pre['vel'],ctrl.phase());why=safety_flags(pre,proj,float(env.damage.damage),0.)
     if why:raise SafetyStop('actual_pre:'+','.join(why))
     if progress is None:progress=old[0]['progress_before'];previous=proj['arc']
     if goal is None or progress>=goal:goal=progress+3.24;deadline=step-1+13
     command=nominal.copy();chosen=None;latency=None
     if step<=118:
      ref=old[step-1]
      if pre!=ref['pre'] or nominal.tolist()!=ref['nominal'] or before!=ref['memory_before']:raise ModelFailure('actual_prefix_sensor_nominal_memory:'+str(step))
      command=np.asarray(ref['command'],np.float32)
     else:
      if step==119:
       start_arc=proj['arc'];ledger=GoalLedger(progress,goal,H-(deadline-(step-1)),round(pre['time']*50));fork=complete_state(env,obs,dict(before=before,after=ctrl.memory(),nominal=nominal.tolist()));save(folder/'fork-private.json',fork)
       if fork!=read(root/'stage418/actual_A/fork-private.json'):raise ModelFailure('actual_fullfork418_mismatch')
       if arm=='P' and fork!=read(d/'actual_C0/fork-private.json'):raise ModelFailure('actual_fullfork_C0_P_mismatch')
      command,chosen,witness,latency=query(root,meter,env,obs,ctrl,fixed,pace,before,nominal,ledger,folder,step,optimize=arm=='P' and step<=121);queries.append(latency);decisions.append(dict(step=step,selected=latency['selected'],decision=latency['decision'],actual_clock=ledger.last_clock_tick))
      witnesses.append(dict(origin=step,rows=witness,active=True,selected=latency['selected']))
      if latency['selected']=='neutralbrake':neutral_steps.append(step)
      if arm=='P' and step<=121:
       model_dec=read(root/'stage421/decisions-private.json');ref=next(z for z in model_dec if z['policy']=='P' and z['relative_decision']==step-118);decisions[-1]['prior421_recipe']=ref['selected_recipe'];decisions[-1]['same_recipe_as421']=ref['selected_recipe']==latency['selected']
     tr.reset();tr.enable();meter.charge('action',arm);t=env.unwrapped.t
     try:obs,_,ended,truncated,info=env.step(command)
     finally:tr.disable()
     post=sensor(env);rt=round((env.unwrapped.t-t)*50);rawstep+=rt;damage=float(env.damage.damage);q=dict(position=post['pos'],velocity=post['vel'],angle=post['angle'],angular_velocity=post['yaw'],speed_m_s=post['speed'],damage=damage,collision=bool(info['collision']),wheel_road_contacts=sum(n>0 for n in post['road_contacts']));postproj,why=metrics(q,tr.rows,tr.hulls,line,ctrl.phase())
     if set(tuple(z) for z in raw_capture_pairs(env))-pairs:why.append('new_obstacle_contact')
     nextprogress=progress+(postproj['arc']-previous+L/2)%L-L/2;hit=nextprogress>=goal or env.unwrapped.finish_time_s is not None
     if step>=deadline and not hit:why.append('actual_progress_deadline')
     row=dict(step=step,pre=pre,post=post,nominal=nominal.tolist(),command=command.tolist(),memory_before=before,nominal_memory_after=ctrl.memory(),raw_ticks=rt,raw_tire_samples=copy.deepcopy(tr.rows),raw_hull=copy.deepcopy(tr.hulls),post_projection=postproj,collision=bool(info['collision']),damage=damage,completed=env.unwrapped.finish_time_s is not None,finish_time_s=env.unwrapped.finish_time_s,ended=bool(ended),truncated=bool(truncated),safety=why,progress_before=progress,progress_after=nextprogress,goal_before=goal,deadline_before=deadline,goal_hit_actual_step=hit,guardian=latency)
     rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush()
     if not validate(row)['passed']:raise ModelFailure('actual_rawtick_terminal_contract')
     if step<=118:
      if row['post']!=old[step-1]['post'] or row['collision']!=old[step-1]['collision'] or row['damage']!=old[step-1]['damage']:raise ModelFailure('actual_prefix_post_exact:'+str(step))
      z=row_fidelity(prefix[step-1],row);checks.append(z)
      if not z['passed']:raise ModelFailure('actual_prefix_source_bodywheelrawhull:'+str(step))
      if arm=='P':
       # EachpriorArowhasexactlythesame physicalhistory, independentreset.
       aref=json.loads((d/'actual_C0/trace-private.jsonl').read_text().splitlines()[step-1])
       for key in ['pre','post','nominal','command','memory_before','nominal_memory_after','raw_tire_samples','raw_hull']:
        if row[key]!=aref[key]:raise ModelFailure('actual_prefix_A_B_fullrow:'+str(step)+':'+key)
      prefixexact+=1
     else:
      z=shapecheck(chosen,row);checks.append(z)
      if not z['passed'] or z['wheel']['clipped_flag_mismatches']!=0:raise ModelFailure('actual_selected_first_bodywheelrawhull_clipping:'+str(step))
      if chosen['memory_after']['C']['phase']!=ctrl.phase():raise ModelFailure('selected_first_controller_phase')
      for w in witnesses:
       offset=step-w['origin']
       if not w['active'] or offset>=len(w['rows']):continue
       f=w['rows'][offset];delta=float(max(abs(command-np.asarray(f['command']))))
       if delta>1e-6:
        w['active']=False;divergences.append(dict(origin=w['origin'],step=step,witness_recipe=w['selected'],actual_recipe=latency['selected'],command_delta=delta,reason='Currentactualpolicychangedcommand; originalwitnessfidelityendsbeforethistransition',guardian_override=latency['selected']=='neutralbrake'));continue
       z=shapecheck(f,row);segment_checks.append(dict(origin=w['origin'],step=step,**z))
       if not z['passed'] or z['wheel']['clipped_flag_mismatches']!=0:raise ModelFailure('actual_matching_witness_bodywheelrawhull_clipping:'+str(step))
      ledger=ledger.advance_actual(ActualObservation(nextprogress,round(post['time']*50),row['completed']))
      if ledger.deadline_missed:raise SafetyStop('actual_committed_ledger_deadline')
      if ledger.progress_m!=nextprogress:raise ModelFailure('actual_ledger_not_committed_observation')
     progress=nextprogress;previous=postproj['arc']
     if why:raise SafetyStop('actual_post:'+','.join(why))
     if row['completed'] or ended or truncated:raise Ineligible('unexpected_terminal_before13')
    status='COMPLETED_SAFE_13'
   except BaseException as e:error=type(e).__name__+': '+str(e);status='CENSORED_STOP';save(folder/'stop-private.json',dict(stage=laststage,error=error,traceback=traceback.format_exc()))
   finally:
    if tr:tr.disable()
    if journal:journal.close()
    if env:save(folder/'final-private.json',complete_state(env,obs,ctrl.memory()));env.close()
   arr=arrival(rows[118:],line,start_arc,p['exit_original_arc']) if status=='COMPLETED_SAFE_13' else dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None);mc,mw=meter.modeltime();rr=dict(arm=arm,status=status,error=error,prefix_exact_rows=prefixexact,suffix_rows=max(0,len(rows)-118),native_actions=meter.nb['actions']-native_before,confirmed_rows=len(rows),unconfirmed_native=meter.nb['actions']-native_before-len(rows),reset_ticks=reset_ticks,raw_step_ticks=rawstep,arrival=arr,damage=rows[-1]['damage'] if rows else None,max_post_path_error_m=max((z['post_projection']['path_error_m'] for z in rows),default=None),neutral_guardian_steps=neutral_steps,model_ticks_during_arm=meter.mb['ticks']-model_before,model_worlds_during_arm=meter.mb['worlds']-world_before,exclusive_actual_CPU_s=time.process_time()-epicpu-(mc-modelc0),exclusive_actual_wall_s=time.perf_counter()-epiwall-(mw-modelw0),query_count=len(queries),query_parent_unchanged_all=all(q['parent_memory_RNG_ledger_unchanged'] for q in queries),selected_first_fidelity_passed=all(z['passed'] for z in checks),matching_recipe_fidelity_rows=len(segment_checks),witness_divergences=divergences,decisions=decisions,actual_ledger=None if ledger is None else asdict(ledger),source_memory_committed=False,original_recipe_command_differences=changed_commands,telemetry=tr.overhead() if tr else None)
   save(folder/'fidelity-checks.json',dict(checks=checks,matching_recipe=segment_checks,witness_divergences=divergences));save(folder/'result.json',rr);results.append(rr)
   if status!='COMPLETED_SAFE_13':break
 finally:meter.end_actual();save(d/'actual-results.json',results);save(d/'query-latencies-private.json',meter.queries)
 return results
