"""Once-only actual C0/P12 carry with staged423 agreement and new selected transition checks."""
import copy,json,math,random,time,traceback
from dataclasses import asdict
import numpy as np
from retry.paired417_common import *
from retry.carry426_model import query
from retry.planner419 import GoalLedger,ActualObservation,H
from retry.fork394_run import complete_state
from retry.loss389_replay import sensor
from retry.pilot398_run import safety_flags,raw_capture_pairs
from retry.terminal409_contract import validate
from retry.guardian426 import actual_done_eligible
def actual_pairs(root,meter,fixed,pace,source,prefix):
 from retry.diagnose import make_env
 d=root/'stage426';p=read(d/'plan.json');line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);old=[json.loads(t) for t in (root/'stage411/policy_C/trace-private.jsonl').read_text().splitlines()];results=[];meter.begin_actual()
 try:
  for arm in ['P']:
   folder=d/('actual_'+arm);folder.mkdir(mode=0o700);env=obs=tr=journal=None;rows=[];checks=[];source_fidelity=[];queries=[];recipe_aligned=True;laststage='reset';error=None;status='STARTED';progress=previous=goal=deadline=None;prefixexact=0;rawstep=reset_ticks=0;start_arc=None;native_before=meter.nb['actions'];model_before=meter.mb['ticks'];world_before=meter.mb['worlds'];neutral_steps=[];changed_commands=[];witnesses=[];segment_checks=[];divergences=[];decisions=[];ledger=None;long_alignment=True;long_break=None;long_command_checks=[];matched423=0;historical_alignment=True;historical_break=None;historical_exact_post_rows=0;initial13exact=False;lap_ms=None;finish_time=None;epicpu=time.process_time();epiwall=time.perf_counter();modelc0,modelw0=meter.modeltime()
   try:
    random.seed(394);np.random.seed(394);env=make_env();meter.charge('reset',arm);obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});ctrl=ActualC(env,fixed,pace);ini=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',ini);start_time=float(env.unwrapped.t)
    if ini!=read(root/('stage425/actual_'+arm+'/initial-private.json')):raise ModelFailure('actual_initial_full_RNG_pixels')
    pairs=set(tuple(z) for z in ini['physical']['touching_obstacle_contacts']);reset_ticks=round(env.unwrapped.t*50);tr=Trace(lambda:env.unwrapped.t);journal=(folder/'trace-private.jsonl').open('x')
    reference425=[json.loads(t) for t in (root/'stage425/actual_P/trace-private.jsonl').read_text().splitlines()];long424=read(root/('stage424/parent_'+arm+'-private.json'))['rows']
    for step in range(1,311):
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
       if fork!=read(root/('stage425/actual_'+arm+'/fork-private.json')):raise ModelFailure('actual_fullfork423_mismatch')
       if arm=='P' and fork!=read(root/'stage425/actual_P/fork-private.json'):raise ModelFailure('actual_fullfork_C0_P_mismatch')
      command,chosen,witness,latency=query(root,meter,env,obs,ctrl,fixed,pace,before,nominal,ledger,folder,step,optimize=arm=='P' and step<=130);queries.append(latency);decisions.append(dict(step=step,selected=latency['selected'],decision=latency['decision'],actual_clock=ledger.last_clock_tick))
      witnesses.append(dict(origin=step,rows=witness,active=True,selected=latency['selected']))
      if latency['selected']=='neutralbrake':neutral_steps.append(step)
      offset=step-119
      if offset<len(long424):
       delta=float(max(abs(command-np.asarray(long424[offset]['command']))));long_command_checks.append(dict(step=step,max_abs_delta=delta,guardian_selected=latency['selected']))
       if long_alignment and delta>1e-6:
        long_alignment=False;long_break=dict(step=step,relative_suffix_action=offset+1,max_abs_delta=delta,guardian_override=latency['selected']=='neutralbrake',reason='Actualselectedcommanddiffersfromoriginal424witness; physicalresultremainsactualpolicy')
      elif long_alignment:
       long_alignment=False;long_break=dict(step=step,relative_suffix_action=offset+1,reason='Original424witnessended; actualnotyetfinished')
      if arm=='P' and step<=130:
       model_dec=read(root/'stage424/decisions-private.json');ref=next(z for z in model_dec if z['policy']=='P' and z['relative_decision']==step-118);decisions[-1]['prior424_recipe']=ref['selected_recipe'];decisions[-1]['same_recipe_as424']=ref['selected_recipe']==latency['selected']
     if step>118 and historical_alignment:
      if step>len(reference425):historical_alignment=False;historical_break=dict(step=step,reason='Historical425trajectoryended')
      else:
       ref=reference425[step-1]
       if command.tolist()!=ref['command']:
        raise ModelFailure('frozen425_command_reproduction_before176:'+str(step))
        historical_alignment=False;historical_break=dict(step=step,relative_suffix_action=step-118,selected_recipe=latency['selected'],max_command_delta=float(max(abs(command-np.asarray(ref['command'])))),pre_state_exact=pre==ref['pre'],memory_before_exact=before==ref['memory_before'],reason='Newactualselectedcommanddiffersfromhistorical425; oldtrajectoryequalityendsbeforethistransition')
        if not historical_break['pre_state_exact'] or not historical_break['memory_before_exact']:raise ModelFailure('historical425_prestate_memory_drift_before_firstchangedcommand')
        if arm=='C0':raise ModelFailure('C0_unexpected_historical425_command_change')
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
     if historical_alignment and step<=len(reference425):
      ref=reference425[step-1]
      for key in ['pre','post','nominal','command','memory_before','nominal_memory_after','raw_ticks','raw_tire_samples','raw_hull','collision','damage','completed','finish_time_s','ended','truncated']:
       if row[key]!=ref[key]:raise ModelFailure('stored423_exact_matching_history:'+str(step)+':'+key)
      matched423+=1;historical_exact_post_rows+=1
     if step<=118:
      if row['post']!=old[step-1]['post'] or row['collision']!=old[step-1]['collision'] or row['damage']!=old[step-1]['damage']:raise ModelFailure('actual_prefix_post_exact:'+str(step))
      z=row_fidelity(prefix[step-1],row);checks.append(z)
      if not z['passed']:raise ModelFailure('actual_prefix_source_bodywheelrawhull:'+str(step))
      if arm=='P':
       # EachpriorArowhasexactlythesame physicalhistory, independentreset.
       aref=json.loads((root/'stage425/actual_P/trace-private.jsonl').read_text().splitlines()[step-1])
       for key in ['pre','post','nominal','command','memory_before','nominal_memory_after','raw_tire_samples','raw_hull']:
        if row[key]!=aref[key]:raise ModelFailure('actual_prefix_A_B_fullrow:'+str(step)+':'+key)
      prefixexact+=1
     else:
      z=shapecheck(chosen,row);checks.append(z)
      if not z['passed'] or z['wheel']['clipped_flag_mismatches']!=0:raise ModelFailure('actual_selected_first_bodywheelrawhull_clipping:'+str(step))
      if chosen['memory_after']['C']['phase']!=ctrl.phase():raise ModelFailure('selected_first_controller_phase')
      for w in witnesses:
       offset=step-w['origin']
       if offset>=len(w['rows']):w['active']=False
       if not w['active']:continue
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
     if step==131:
      boundary=complete_state(env,obs,ctrl.memory());save(folder/'after13-private.json',boundary)
      if historical_alignment:
       if boundary!=read(root/('stage425/actual_'+arm+'/after13-private.json')):raise ModelFailure('stored423_matching_full_after13_state_RNG_memory_pixels')
       initial13exact=True
     if row['completed']:
      if not actual_done_eligible(row,True):raise ModelFailure('actual_DONE_requires_dispatched_native_finish')
      ctrl.done(env);finish_time=float(env.unwrapped.finish_time_s);lap_ms=round((finish_time-start_time)*1000);status='COMPLETED_SAFE_OFFICIAL';break
     if ended or truncated:raise Ineligible('nonfinish_actual_terminal_no_time_imputation')
    else:status='PER_ARM310_COST_CENSORED'
   except BaseException as e:error=type(e).__name__+': '+str(e);status='CENSORED_STOP';save(folder/'stop-private.json',dict(stage=laststage,error=error,traceback=traceback.format_exc()))
   finally:
    if tr:tr.disable()
    if journal:journal.close()
    if env:save(folder/'final-private.json',complete_state(env,obs,ctrl.memory()));env.close()
   arr=arrival(rows[118:],line,start_arc,p['exit_original_arc']) if start_arc is not None and len(rows)>118 else dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None);mc,mw=meter.modeltime();rr=dict(arm=arm,status=status,error=error,prefix_exact_rows=prefixexact,suffix_rows=max(0,len(rows)-118),historical425_exact_rows=matched423,historical425_first_command_break=historical_break,historical425_alignment_until_end=historical_alignment,initial13_full_after_state_exact=initial13exact,completed=status=='COMPLETED_SAFE_OFFICIAL',lap_ms=lap_ms,official_finish_time_s=finish_time,start_time_s=start_time if env else None,original424_command_alignment_until_end=long_alignment,original424_first_command_break=long_break,original424_command_comparisons=long_command_checks,native_actions=meter.nb['actions']-native_before,confirmed_rows=len(rows),unconfirmed_native=meter.nb['actions']-native_before-len(rows),reset_ticks=reset_ticks,raw_step_ticks=rawstep,arrival=arr,damage=rows[-1]['damage'] if rows else None,max_post_path_error_m=max((z['post_projection']['path_error_m'] for z in rows),default=None),neutral_guardian_steps=neutral_steps,model_ticks_during_arm=meter.mb['ticks']-model_before,model_worlds_during_arm=meter.mb['worlds']-world_before,exclusive_actual_CPU_s=time.process_time()-epicpu-(mc-modelc0),exclusive_actual_wall_s=time.perf_counter()-epiwall-(mw-modelw0),query_count=len(queries),query_parent_unchanged_all=all(q['parent_memory_RNG_ledger_unchanged'] for q in queries),selected_first_fidelity_passed=all(z['passed'] for z in checks),matching_recipe_fidelity_rows=len(segment_checks),witness_divergences=divergences,decisions=decisions,actual_ledger=None if ledger is None else asdict(ledger),source_memory_committed=False,original_recipe_command_differences=changed_commands,telemetry=tr.overhead() if tr else None)
   save(folder/'fidelity-checks.json',dict(checks=checks,matching_recipe=segment_checks,witness_divergences=divergences));print(json.dumps(dict(stage=426,arm=arm,status=status,error=error,actions=len(rows),lap_ms=lap_ms,model_ticks=meter.b['ticks'],model_worlds=meter.b['worlds'])),flush=True);save(folder/'result.json',rr);results.append(rr)
   if status!='COMPLETED_SAFE_OFFICIAL':break
 finally:meter.end_actual();save(d/'actual-results.json',results);save(d/'query-latencies-private.json',meter.queries)
 return results
