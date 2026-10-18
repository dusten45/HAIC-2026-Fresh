"""Preregistered corrected-model danger rejection, precursor probe and full pair."""
import datetime,hashlib,json,math,signal,time
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.cap529_control import path_for
from retry.response528_control import choose
from retry.drive519_control import project,nominal,steering,reference,force_rows
from retry.closure524_control import tick
from retry.plan513_model import load_root
from retry.lap518_finish import hull_pose,tracker_for
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response529-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();counter=[0];cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0);c=json.loads((G/'retry/cap529_contract.json').read_text())
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
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths={v:path_for(static,v) for v in ('baseline','comparison','candidate','backup')};ledger=json.loads(Path('/workspace/haic-response519-private/model-ledger-private.json').read_text());index=bounds(static['roads']);ei=boundary_index(static['boundary'])
    assert json.loads(json.dumps(paths['baseline']))==json.loads(Path('/workspace/haic-response525-private/frozen-paths-private.json').read_text())['governor']
    excluded=('periodic_squared','launch_squared','periodic_pass_rounds');assert {k:v for k,v in paths['baseline'].items() if k not in excluded}=={k:v for k,v in paths['candidate'].items() if k not in excluded}
    save(D/'frozen-paths-private.json',paths);save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/cap529_contract.json').read_bytes()).hexdigest()))
    def root_from(p):
        x=json.loads(Path(p).read_text())['before_root_without_roads'];x['roads']=static['root']['roads'];return load_root(x)
    history_ledger=json.loads((D/'current-ledger-private.json').read_text());danger_rejected=True
    def simulate(root,variant,completed,visited,full,limit,case=None):
        path=paths[variant];s=project(root.center,path,case['progress'] if case else ledger['anchor'] if completed else None)['s'];tracker=tracker_for(static,root,visited,completed>0,1.02+.08*completed) if full else None;elapsed=0.;trace=[];commands=[];minimum=margin(root,static['roads'],index,static['boundary'],ei,static['obstacles']);maxpath=maxover=maxspeed=maxbody=0.;stats={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')};modes={};failure=None;stop='PROBE_COMPLETE' if not full else 'MAX500'
        prefix=dict(clipped=case['clipped'],samples=case['samples']) if case else dict(clipped=0,samples=352 if completed else 0)
        stats['running']['clipped']=prefix['clipped'];stats['running']['samples']=prefix['samples']
        for i in range(completed,min(500,completed+limit)):
            guard()
            if i<24:action=np.array([steering(root,path,s),.32,0],np.float32);detail=dict(mode='FIXED_LAUNCH')
            else:action,detail=choose(root,path,paths['backup'],s,counter,cost,history=(stats['running']['clipped'],stats['running']['samples']))
            if action is None:failure=dict(action_index=i+1,reason='NO_ADMISSIBLE_ACTION');stop='NO_ADMISSIBLE_ACTION';commands.append(dict(index=i+1,detail=detail));break
            modes[detail['mode']]=modes.get(detail['mode'],0)+1;commands.append(dict(index=i+1,action=action.tolist(),detail=detail));root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
            for k in range(4):
                if counter[0]>=120000:raise RuntimeError('MODEL_TICK_CAP_525')
                before=root;old_s=s;force=force_rows(root,action);cost['force_evaluations']+=4;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);elapsed+=.02;q=project(root.center,path,s);s=q['s'];maxspeed=max(maxspeed,math.hypot(*root.planar.linear.velocity));maxbody=max(maxbody,max(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels),math.hypot(*hull_pose(root)[1]));gap=margin(root,static['roads'],index,static['boundary'],ei,static['obstacles']);minimum=min(minimum,gap);maxpath=max(maxpath,q['distance']);target,ff=reference(s,path);over=math.hypot(*root.planar.linear.velocity)-target
                if i>=24:maxover=max(maxover,over)
                group='launch' if i<24 else 'running';z=stats[group];z['peak']=max(z['peak'],max(w['ratio'] for w in force));z['samples']+=4;z['clipped']+=sum(w['clipped'] for w in force)
                for ids in root.current_contacts:visited.update(ids)
                if tracker:
                    pos,vel=hull_pose(root);tracker.update(pos,vel,len(visited)/len(static['track']),1.02+.08*completed+elapsed)
                state=asdict(root);state.pop('roads');trace.append(dict(index=i+1,raw=k+1,root_without_roads=state,progress=s,margin=gap,path_error=q['distance'],target=target,forces=force,action=action.tolist()))
                problems=[]
                if maxbody>=100.:problems.append('BOX2D_TRANSLATION_MODEL_DOMAIN')
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
        out=dict(max_speed_m_s=maxspeed,max_body_speed_m_s=maxbody,end_progress=s,history_samples_before=prefix['samples'],variant=variant,completed_before=completed,stop=stop,raw_ticks=len(trace),actions=len(commands),force_groups=stats,min_margin_m=minimum,max_path_error_m=maxpath,max_reference_overspeed_m_s=maxover,mode_counts=modes,high_fraction=high_fraction,first_failure=failure,model_finish_episode_s=tracker.finish_time_s-1.02 if tracker and tracker.finish_time_s is not None else None,pass_safety=failure is None and stop==('MODEL_SOURCE_STYLE_FINISH' if full else 'PROBE_COMPLETE'))
        return out,trace,commands
    probes=[]
    for case in history_ledger['probes']:
        pair=[]
        for v in ('comparison','candidate'):
            state=dict(case['root_without_roads']);state['roads']=static['root']['roads'];item,trace,commands=simulate(load_root(state),v,case['completed'],set(),False,case['holds'],case)
            save(D/f"probe-{case['label']}-{v}-private.json",dict(summary=item,trace=trace,commands=commands));pair.append(item)
        progress_gain=pair[1]['end_progress']-pair[0]['end_progress'];speed_gain=pair[1]['max_speed_m_s']-pair[0]['max_speed_m_s'];passed=all(z['pass_safety'] and z['raw_ticks']==4*case['holds'] for z in pair) and (case['label']!='cap_entry' or (progress_gain>=1. and speed_gain>=1.))
        probes.append(dict(label=case['label'],arms=pair,progress_gain_m=progress_gain,peak_speed_gain_m_s=speed_gain,pass_gate=passed))
    probe_pass=all(z['pass_gate'] for z in probes) and len(probes)==2
    arms=[];cold_gain=carry_gain=None;direct_cap_gain=None;direct_carry_gain=None;comparison_carry=None
    if probe_pass:
        for start in ('cold','carry'):
            if start=='carry' and (cold_gain is None or cold_gain<.5 or not all(z['pass_safety'] for z in arms)):break
            cache=json.loads(Path(history_ledger['cached_models'][start]).read_text())['summary'];assert cache['variant']=='governor' and cache['pass_safety'];arms.append(dict(cache,variant='baseline',reused_model=True))
            if start=='cold':root=load_root(static['root']);completed=0;visited=set(ledger['initial_visited'])
            else:root=root_from(ledger['checkpoint']);completed=ledger['completed_actions'];visited=set(ledger['carry_visited'])
            if start=='carry':
                comparison_carry,comp_trace,comp_commands=simulate(root,'comparison',completed,set(visited),True,500);save(D/'carry-comparison-model-private.json',dict(summary=comparison_carry,trace=comp_trace,commands=comp_commands))
                if not comparison_carry['pass_safety']:break
            item,trace,commands=simulate(root,'candidate',completed,visited,True,500);item['start']=start;save(D/f'{start}-candidate-model-private.json',dict(summary=item,trace=trace,commands=commands));arms.append(item)
            if not item['pass_safety']:break
            gain=cache['model_finish_episode_s']-item['model_finish_episode_s']
            if start=='cold':cold_gain=gain;direct_cap_gain=18.00-item['model_finish_episode_s']
            else:carry_gain=gain;direct_carry_gain=comparison_carry['model_finish_episode_s']-item['model_finish_episode_s']
    eligible=probe_pass and len(arms)==4 and all(z['pass_safety'] for z in arms) and cold_gain>=.5 and carry_gain>=.5 and arms[1]['high_fraction']>=.5 and arms[3]['high_fraction']>=.5 and direct_cap_gain>0 and direct_carry_gain>=0
    out=dict(status='CORRECTED_MODEL_NATIVE_ELIGIBLE' if eligible else 'CORRECTED_MODEL_NOT_PROMOTED',native_pair_eligible=eligible,probe_pass=probe_pass,probe=probes,arms=arms,cold_finish_gain_s=cold_gain,carry_finish_gain_s=carry_gain,direct_cap_cold_gain_vs528_s=direct_cap_gain,direct_cap_carry_gain_vs528_s=direct_carry_gain,comparison_528_carry=comparison_carry,model_integrator_ticks=counter[0],source_wheel_force_evaluations_in_integrator=4*counter[0],explicit_force_evaluations=cost['force_evaluations'],planner_cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,native_resets=0,research_remaining=24155,reserve=84000,reserve_used=0,scope='529onlyprimarycap80to90 vs528, allgovernor/paths/forward/back80/backupunchanged; primarypromotionvs52518.40. No actual528validationclaim. Box2D100perbodymodeldomainchecked.')
    assert counter[0]<=120000 and cost['force_evaluations']<=600000;guard();save(G/'retry/cap529_model_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':run()
