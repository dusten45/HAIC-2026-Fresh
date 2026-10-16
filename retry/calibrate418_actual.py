"""Independent actual calibration; frozenhistory118, signedC13 with identical411 safety guardian."""
import copy,json,math,random,time,traceback
import numpy as np
from retry.paired417_common import *
from retry.fork394_run import complete_state
from retry.terminal410_model import from_actual_full
from retry.loss389_replay import sensor
from retry.pilot398_run import safety_flags,raw_capture_pairs
from retry.terminal409_contract import validate

def guardian(root,meter,env,obs,ctrl,fixed,pace,before,nominal,step,progress,goal,deadline,folder,fullgas=False):
 cpu=time.process_time();wall=time.perf_counter()
 with meter.model('guardian_'+folder.name+'_'+str(step)):
  full=complete_state(env,obs,ctrl.memory());h=fingerprint(full);state=from_actual_full(full);mh=fingerprint(ctrl.memory());fs={}
  def pair(name,recipe):
   a=forecast(meter,state,before,fixed,pace,step-1,progress,goal,deadline,recipe);b=forecast(meter,state,before,fixed,pace,step-1,progress,goal,deadline,recipe)
   if sig(a)!=sig(b):raise ModelFailure('actual_guardian_independence:'+name)
   if fingerprint(complete_state(env,obs,ctrl.memory()))!=h or fingerprint(ctrl.memory())!=mh:raise ModelFailure('LIVE_actual_parent_memory_RNG_mutation')
   fs[name]=a;return a
  primary=pair('nominal','nominal');selected='nominal';chosen=primary
  if not primary['valid']:
   pulse=pair('neutralbrake','neutralbrake')
   if not pulse['valid']:raise Ineligible('guardian_both_recipes_ineligible')
   chosen=pulse;selected='neutralbrake'
  if fullgas:
   # Frozen B first intervention itself must pass same current-state predicate.
   candidate=pair('fixed_fullgas','fullgas')
   if not candidate['valid']:raise Ineligible('B_first_fullgas_ineligible_no_replacement')
   chosen=candidate;selected='fixed_fullgas'
  if not chosen['rows']:raise Ineligible('no_first_prediction')
  command=np.asarray(chosen['rows'][0]['command'],np.float32)
  if selected=='nominal' and max(abs(command-nominal))>1e-6:raise ModelFailure('guardian_current_nominal_mismatch')
  save(folder/('guardian-'+str(step)+'-private.json'),dict(forecasts=fs,selected=selected,parent_before_sha256=h,parent_after_sha256=h,memory_unchanged=True))
 latency=dict(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,selected=selected,nominal_valid=primary['valid'],parent_unchanged=True,model_ticks=meter.mb['ticks'],worlds=meter.mb['worlds'])
 meter.queries.append(dict(arm=folder.name,step=step,**latency));return command,chosen,latency

def actual_pairs(root,meter,fixed,pace,source,prefix):
 from retry.diagnose import make_env
 d=root/'stage418';p=read(d/'plan.json');line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);old=[json.loads(t) for t in (root/'stage411/policy_C/trace-private.jsonl').read_text().splitlines()];results=[];meter.begin_actual()
 try:
  for arm in ['A','B']:
   folder=d/('actual_'+arm);folder.mkdir(mode=0o700);env=obs=tr=journal=None;rows=[];checks=[];source_fidelity=[];queries=[];recipe_aligned=True;laststage='reset';error=None;status='STARTED';progress=previous=goal=deadline=None;prefixexact=0;rawstep=reset_ticks=0;start_arc=None;native_before=meter.nb['actions'];model_before=meter.mb['ticks'];world_before=meter.mb['worlds'];neutral_steps=[];changed_commands=[];epicpu=time.process_time();epiwall=time.perf_counter();modelc0,modelw0=meter.modeltime()
   try:
    random.seed(394);np.random.seed(394);env=make_env();meter.charge('reset',arm);obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});ctrl=ActualC(env,fixed,pace);ini=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',ini)
    if ini!=read(root/'stage411/policy_C/initial-private.json'):raise ModelFailure('actual_initial_full_RNG_pixels')
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
       start_arc=proj['arc'];fork=complete_state(env,obs,dict(before=before,after=ctrl.memory(),nominal=nominal.tolist()));save(folder/'fork-private.json',fork)
       if arm=='B' and fork!=read(d/'actual_A/fork-private.json'):raise ModelFailure('actual_fullfork_A_B_mismatch')
      command,chosen,latency=guardian(root,meter,env,obs,ctrl,fixed,pace,before,nominal,step,progress,goal,deadline,folder,fullgas=arm=='B' and step==119);queries.append(latency)
      if latency['selected']=='neutralbrake':neutral_steps.append(step);recipe_aligned=False
      if command.tolist()!=source[arm]['rows'][step-119]['command']:changed_commands.append(dict(step=step,actual=command.tolist(),source=source[arm]['rows'][step-119]['command'],max_abs_delta=float(max(abs(command-np.asarray(source[arm]['rows'][step-119]['command'])))),selection=latency['selected']))
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
      if arm=='B':
       # EachpriorArowhasexactlythesame physicalhistory, independentreset.
       aref=json.loads((d/'actual_A/trace-private.jsonl').read_text().splitlines()[step-1])
       for key in ['pre','post','nominal','command','memory_before','nominal_memory_after','raw_tire_samples','raw_hull']:
        if row[key]!=aref[key]:raise ModelFailure('actual_prefix_A_B_fullrow:'+str(step)+':'+key)
      prefixexact+=1
     else:
      z=row_fidelity(chosen['rows'][0],row);checks.append(z)
      if not z['passed']:raise ModelFailure('actual_selected_first_bodywheelrawhull:'+str(step))
      if recipe_aligned:
       f=source[arm]['rows'][step-119];delta=max(abs(command-np.asarray(f['command'])))
       if delta>1e-6:raise ModelFailure('original_recipe_command_drift:'+str(step))
       z=row_fidelity(f,row);source_fidelity.append(dict(step=step,**z))
       if not z['passed']:raise ModelFailure('actual_matching_recipe_horizon_fidelity:'+str(step))
     progress=nextprogress;previous=postproj['arc']
     if why:raise SafetyStop('actual_post:'+','.join(why))
     if row['completed'] or ended or truncated:raise Ineligible('unexpected_terminal_before13')
    status='COMPLETED_SAFE_13'
   except BaseException as e:error=type(e).__name__+': '+str(e);status='CENSORED_STOP';save(folder/'stop-private.json',dict(stage=laststage,error=error,traceback=traceback.format_exc()))
   finally:
    if tr:tr.disable()
    if journal:journal.close()
    if env:save(folder/'final-private.json',complete_state(env,obs,ctrl.memory()));env.close()
   arr=arrival(rows[118:],line,start_arc,p['exit_original_arc']) if status=='COMPLETED_SAFE_13' else dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None);mc,mw=meter.modeltime();rr=dict(arm=arm,status=status,error=error,prefix_exact_rows=prefixexact,suffix_rows=max(0,len(rows)-118),native_actions=meter.nb['actions']-native_before,confirmed_rows=len(rows),unconfirmed_native=meter.nb['actions']-native_before-len(rows),reset_ticks=reset_ticks,raw_step_ticks=rawstep,arrival=arr,damage=rows[-1]['damage'] if rows else None,max_post_path_error_m=max((z['post_projection']['path_error_m'] for z in rows),default=None),neutral_guardian_steps=neutral_steps,model_ticks_during_arm=meter.mb['ticks']-model_before,model_worlds_during_arm=meter.mb['worlds']-world_before,exclusive_actual_CPU_s=time.process_time()-epicpu-(mc-modelc0),exclusive_actual_wall_s=time.perf_counter()-epiwall-(mw-modelw0),query_count=len(queries),query_parent_unchanged_all=all(q['parent_unchanged'] for q in queries),selected_first_fidelity_passed=all(z['passed'] for z in checks),matching_recipe_fidelity_rows=len(source_fidelity),original_recipe_command_differences=changed_commands,telemetry=tr.overhead() if tr else None)
   save(folder/'fidelity-checks.json',dict(checks=checks,matching_recipe=source_fidelity));save(folder/'result.json',rr);results.append(rr)
   if status!='COMPLETED_SAFE_13':break
 finally:meter.end_actual();save(d/'actual-results.json',results);save(d/'query-latencies-private.json',meter.queries)
 return results
