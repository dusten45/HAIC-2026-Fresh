"""Preregistered corrected-model danger rejection, precursor probe and full pair."""
import datetime,hashlib,json,math,signal,time
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.braking526_control import path_for
from retry.response528_control import choose
from retry.drive519_control import project,nominal,steering,reference,force_rows
from retry.closure524_control import tick
from retry.plan513_model import load_root
from retry.lap518_finish import hull_pose,tracker_for
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response528-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();counter=[0];cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0);c=json.loads((G/'retry/response528_contract.json').read_text())
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_MODEL_RETRY')
    def save(p,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode()
        if len(list(D.iterdir()))>=8192 or sum(z.stat().st_size for z in D.iterdir())+len(data)>256*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def guard():
        if time.process_time()-cpu>=360 or time.perf_counter()-wall>=480:raise RuntimeError('MODEL_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,360)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,480)
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_IN_MODEL')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=Car.__init__=poison
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths={v:path_for(static,v) for v in ('baseline','candidate','backup')};ledger=json.loads(Path('/workspace/haic-response519-private/model-ledger-private.json').read_text());index=bounds(static['roads']);ei=boundary_index(static['boundary'])
    assert json.loads(json.dumps(paths['baseline']))==json.loads(Path('/workspace/haic-response525-private/frozen-paths-private.json').read_text())['governor']
    excluded=('periodic_squared','launch_squared','periodic_pass_rounds');assert {k:v for k,v in paths['baseline'].items() if k not in excluded}=={k:v for k,v in paths['candidate'].items() if k not in excluded}
    save(D/'frozen-paths-private.json',paths);save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/response528_contract.json').read_bytes()).hexdigest()))
    def root_from(p):
        x=json.loads(Path(p).read_text())['before_root_without_roads'];x['roads']=static['root']['roads'];return load_root(x)
    history_ledger=json.loads((D/'current-ledger-private.json').read_text());danger_rejected=True
    def simulate(root,variant,completed,visited,full,limit):
        path=paths[variant];s=project(root.center,path,ledger['anchor'] if completed else None)['s'];tracker=tracker_for(static,root,visited,completed>0,1.02+.08*completed) if full else None;elapsed=0.;trace=[];commands=[];minimum=margin(root,static['roads'],index,static['boundary'],ei,static['obstacles']);maxpath=maxover=0.;stats={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')};modes={};failure=None;stop='PROBE_COMPLETE' if not full else 'MAX500'
        prefix=dict(clipped=0,samples=352 if completed else 0)
        stats['running']['clipped']=prefix['clipped'];stats['running']['samples']=prefix['samples']
        for i in range(completed,min(500,completed+limit)):
            guard()
            if i<24:action=np.array([steering(root,path,s),.32,0],np.float32);detail=dict(mode='FIXED_LAUNCH')
            else:action,detail=choose(root,path,paths['backup'],s,counter,cost,history=(stats['running']['clipped'],stats['running']['samples']))
            if action is None:failure=dict(action_index=i+1,reason='NO_ADMISSIBLE_ACTION');stop='NO_ADMISSIBLE_ACTION';commands.append(dict(index=i+1,detail=detail));break
            modes[detail['mode']]=modes.get(detail['mode'],0)+1;commands.append(dict(index=i+1,action=action.tolist(),detail=detail));root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
            for k in range(4):
                if counter[0]>=120000:raise RuntimeError('MODEL_TICK_CAP_525')
                before=root;old_s=s;force=force_rows(root,action);cost['force_evaluations']+=4;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);elapsed+=.02;q=project(root.center,path,s);s=q['s'];gap=margin(root,static['roads'],index,static['boundary'],ei,static['obstacles']);minimum=min(minimum,gap);maxpath=max(maxpath,q['distance']);target,ff=reference(s,path);over=math.hypot(*root.planar.linear.velocity)-target
                if i>=24:maxover=max(maxover,over)
                group='launch' if i<24 else 'running';z=stats[group];z['peak']=max(z['peak'],max(w['ratio'] for w in force));z['samples']+=4;z['clipped']+=sum(w['clipped'] for w in force)
                for ids in root.current_contacts:visited.update(ids)
                if tracker:
                    pos,vel=hull_pose(root);tracker.update(pos,vel,len(visited)/len(static['track']),1.02+.08*completed+elapsed)
                state=asdict(root);state.pop('roads');trace.append(dict(index=i+1,raw=k+1,root_without_roads=state,progress=s,margin=gap,path_error=q['distance'],target=target,forces=force,action=action.tolist()))
                problems=[]
                if gap<.5:problems.append('MARGIN')
                if maxpath>3:problems.append('PATH_ERROR')
                if maxover>5:problems.append('REFERENCE_OVERSPEED')
                if s-old_s<-.5 or s-old_s>max(5.,2*math.dist(root.center,before.center)):problems.append('PROJECTION')
                if stats['launch']['peak']>2.5 or (i>=23 and stats['launch']['samples'] and stats['launch']['clipped']/stats['launch']['samples']>.15):problems.append('LAUNCH_FORCE')
                if stats['running']['peak']>1.25 or (stats['running']['samples'] and stats['running']['clipped']/stats['running']['samples']>.10):problems.append('RUNNING_FORCE')
                if stats['running']['peak']>1.06:problems.append('UNCERTAINTY_MARGIN')
                if problems:failure=dict(action_index=i+1,raw_in_hold=k+1,episode_s=.08*completed+elapsed,violations=problems);stop=problems[0];break
                if tracker and tracker.finish_time_s is not None:stop='MODEL_SOURCE_STYLE_FINISH';break
                if full and 50+4*completed+len(trace)>=1224:stop='TIME_LIMIT';break
                if s>path['length']+10 and tracker and tracker.finish_time_s is None:stop='ARC_WITHOUT_FINISH';break
            if failure or stop in ('MODEL_SOURCE_STYLE_FINISH','TIME_LIMIT','ARC_WITHOUT_FINISH'):break
        high_fraction=modes.get('HIGH',0)/max(1,sum(v for key,v in modes.items() if key!='FIXED_LAUNCH'))
        out=dict(end_progress=s,history_samples_before=prefix['samples'],variant=variant,completed_before=completed,stop=stop,raw_ticks=len(trace),actions=len(commands),force_groups=stats,min_margin_m=minimum,max_path_error_m=maxpath,max_reference_overspeed_m_s=maxover,mode_counts=modes,high_fraction=high_fraction,first_failure=failure,model_finish_episode_s=tracker.finish_time_s-1.02 if tracker and tracker.finish_time_s is not None else None,pass_safety=failure is None and stop==('MODEL_SOURCE_STYLE_FINISH' if full else 'PROBE_COMPLETE'))
        return out,trace,commands
    # Newsource-responsecommands vs immutable527coarsebackup on sharedroots.
    probes=[]
    for case in history_ledger['probes']:
        state=dict(case['root_without_roads']);state['roads']=static['root']['roads'];root=load_root(state);path=paths['candidate'];s=case['progress'];action,detail=choose(root,path,paths['backup'],s,counter,cost,history=(case['clipped'],case['samples']));trace=[];peak=over=0.;gap=margin(root,static['roads'],index,static['boundary'],ei,static['obstacles']);deficit=None
        if action is not None:
            root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
            for k in range(4):
                force=force_rows(root,action);cost['force_evaluations']+=4;peak=max(peak,max(w['ratio'] for w in force));root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);q=project(root.center,path,s);s=q['s'];target=reference(s,path)[0];speed=math.hypot(*root.planar.linear.velocity);over=max(over,speed-target);gap=min(gap,margin(root,static['roads'],index,static['boundary'],ei,static['obstacles']));deficit=max(0.,target-speed);trace.append(dict(raw=k+1,forces=force,progress=s,speed=speed,reference=target))
        same=action is not None and np.array_equal(action,np.asarray(case['old_command'],np.float32));improvement=case['old_end_positive_deficit']-deficit if deficit is not None else None
        safety=action is not None and peak<=1.06 and over<=5 and gap>=.5 and detail['final_recertified']
        passed=safety and ((case['label']=='normal' and detail['mode']=='HIGH' and same) or (case['label']!='normal' and improvement>=.10))
        if case['label']=='boundary':passed=passed and deficit<=.5*case['old_end_positive_deficit']
        item=dict(label=case['label'],index=case['index'],mode=detail['mode'],old_action_unchanged=same,raw_ticks=len(trace),peak=peak,max_reference_overspeed=over,min_margin=gap,old_end_deficit=case['old_end_positive_deficit'],new_end_deficit=deficit,deficit_reduction=improvement,pass_gate=bool(passed),coarse_nonmonotone=detail.get('coarse_nonmonotone',False),numerical_calls=detail.get('numerical_calls',0));probes.append(item);save(D/f"probe-{case['label']}-private.json",dict(summary=item,detail=detail,trace=trace,selected_action=action.tolist() if action is not None else None))
    improvements=[z['deficit_reduction'] for z in probes if z['label']!='normal'];probe_pass=all(z['pass_gate'] for z in probes) and len(probes)==3 and sum(improvements)/2>=.5
    arms=[];cold_gain=carry_gain=None
    if probe_pass:
        for start in ('cold','carry'):
            if start=='carry' and (cold_gain is None or cold_gain<.5 or not all(z['pass_safety'] for z in arms)):break
            cache=json.loads(Path(history_ledger['cached_models'][start]).read_text())['summary'];assert cache['variant']=='governor' and cache['pass_safety'];arms.append(dict(cache,variant='baseline',reused_model=True))
            if start=='cold':root=load_root(static['root']);completed=0;visited=set(ledger['initial_visited'])
            else:root=root_from(ledger['checkpoint']);completed=ledger['completed_actions'];visited=set(ledger['carry_visited'])
            item,trace,commands=simulate(root,'candidate',completed,visited,True,500);item['start']=start;save(D/f'{start}-candidate-model-private.json',dict(summary=item,trace=trace,commands=commands));arms.append(item)
            if not item['pass_safety']:break
            gain=cache['model_finish_episode_s']-item['model_finish_episode_s']
            if start=='cold':cold_gain=gain
            else:carry_gain=gain
    eligible=probe_pass and len(arms)==4 and all(z['pass_safety'] for z in arms) and cold_gain>=.5 and carry_gain>=.5 and arms[1]['high_fraction']>=.5 and arms[3]['high_fraction']>=.5
    out=dict(status='CORRECTED_MODEL_NATIVE_ELIGIBLE' if eligible else 'CORRECTED_MODEL_NOT_PROMOTED',native_pair_eligible=eligible,probe_pass=probe_pass,probe=probes,arms=arms,cold_finish_gain_s=cold_gain,carry_finish_gain_s=carry_gain,model_integrator_ticks=counter[0],source_wheel_force_evaluations_in_integrator=4*counter[0],explicit_force_evaluations=cost['force_evaluations'],planner_cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,native_resets=0,research_remaining=24155,reserve=84000,reserve_used=0,scope='528source-responsefirstpedalsearch, allfloat32trialscertified12holds/finalfresh. Same527back80/reference/steering and524model;benchmark52518.40. Internaltrackingreserve.15fromexistingpredictionallowance,actualgate5/margin.19/force1.25unchanged.')
    assert counter[0]<=120000 and cost['force_evaluations']<=600000;guard();save(G/'retry/response528_model_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':run()
