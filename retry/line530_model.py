"""One frozen racing-line candidate, geometry/risk/cold/carry gates in order."""
import datetime,hashlib,json,math,signal,time
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.response528_control import choose
from retry.drive519_control import project,steering,reference,force_rows
from retry.closure524_control import tick
from retry.plan513_model import load_root
from retry.lap518_finish import hull_pose,tracker_for
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response530-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();counter=[0];cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0);c=json.loads((G/'retry/line530_contract.json').read_text());registration=json.loads((D/'model-registration-private.json').read_text());design=json.loads((G/'retry/line530_design.json').read_text())
    assert design['pass_design_gate']
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_MODEL_RETRY')
    def save(p,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode()
        if len(list(D.iterdir()))>=8192 or sum(z.stat().st_size for z in D.iterdir())+len(data)>256*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def guard():
        if time.process_time()-cpu>=360 or time.perf_counter()-wall>=480:raise RuntimeError('MODEL_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
        if cost['force_evaluations']>600000 or counter[0]>120000:raise RuntimeError('MODEL_WORK_CAP')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,360)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,480)
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    assert hashlib.sha256((G/'retry/line530_model.py').read_bytes()).hexdigest()==registration['model_source_sha256']
    assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==design['frozen_paths_sha256']==registration['paths_sha256']
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_IN_MODEL')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=Car.__init__=poison
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());ledger=json.loads(Path('/workspace/haic-response519-private/model-ledger-private.json').read_text());index=bounds(static['roads']);ei=boundary_index(static['boundary'])
    assert paths['baseline']==json.loads(Path('/workspace/haic-response528-private/frozen-paths-private.json').read_text())['candidate']
    assert paths['baseline_backup']==json.loads(Path('/workspace/haic-response528-private/frozen-paths-private.json').read_text())['backup']
    save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/line530_contract.json').read_bytes()).hexdigest(),registration=registration))
    def root_from(p):
        x=json.loads(Path(p).read_text())['before_root_without_roads'];x['roads']=static['root']['roads'];return load_root(x)
    def simulate(root,variant,completed,visited,full,limit,case=None):
        path=paths[variant];s=project(root.center,path,None)['s'];tracker=tracker_for(static,root,visited,completed>0,1.02+.08*completed) if full else None;elapsed=0.;trace=[];commands=[];minimum=margin(root,static['roads'],index,static['boundary'],ei,static['obstacles']);maxpath=maxover=maxspeed=maxbody=0.;stats={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')};modes={};failure=None;stop='PROBE_COMPLETE' if not full else 'MAX500'
        prefix=dict(clipped=case['history']['clipped'],samples=case['history']['samples']) if case else dict(clipped=0,samples=352 if completed else 0)
        stats['running']['clipped']=prefix['clipped'];stats['running']['samples']=prefix['samples']
        for i in range(completed,min(500,completed+limit)):
            guard()
            if cost['force_evaluations']+6200>600000:raise RuntimeError('FORCE_CAP_RESERVE')
            if i<24:action=np.array([steering(root,path,s),.32,0],np.float32);detail=dict(mode='FIXED_LAUNCH')
            else:action,detail=choose(root,path,paths['baseline_backup'] if variant=='baseline' else paths['backup'],s,counter,cost,history=(stats['running']['clipped'],stats['running']['samples']))
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
    for case in json.loads((D/'risks-private.json').read_text()):
        pair=[]
        for v in ('baseline','candidate'):
            state=dict(case['root_without_roads']);state['roads']=static['root']['roads'];item,trace,commands=simulate(load_root(state),v,case['index']-1,set(),False,case['holds'],case)
            save(D/f"probe-{case['label']}-{v}-private.json",dict(summary=item,trace=trace,commands=commands));pair.append(item)
            if not item['pass_safety']:break
        passed=len(pair)==2 and all(x['pass_safety'] and x['raw_ticks']==96 for x in pair)
        probes.append(dict(label=case['label'],arms=pair,pass_gate=passed))
        if not passed:break
    probe_pass=len(probes)==2 and all(x['pass_gate'] for x in probes);arms=[];cold_gain=carry_gain=direct_cold_gain=direct_carry_gain=None;comparison_carry=None
    cache528=json.loads(Path('/workspace/haic-response528-private/cold-candidate-model-private.json').read_text())['summary']
    if probe_pass:
        for start in ('cold','carry'):
            if start=='carry' and (cold_gain is None or cold_gain<.50 or direct_cold_gain<.10 or not arms[-1]['pass_safety'] or arms[-1]['high_fraction']<.5):break
            cache525=json.loads(Path('/workspace/haic-response525-private/'+('cold-governor-B-model-private.json' if start=='cold' else 'carry-governor-B-model-private.json')).read_text())['summary']
            if start=='cold':root=load_root(static['root']);completed=0;visited=set(ledger['initial_visited'])
            else:
                root=root_from(ledger['checkpoint']);completed=ledger['completed_actions'];visited=set(ledger['carry_visited'])
                comparison_carry,trace,commands=simulate(root,'baseline',completed,set(visited),True,500)
                save(D/'carry-baseline528-model-private.json',dict(summary=comparison_carry,trace=trace,commands=commands))
                if not comparison_carry['pass_safety']:break
            item,trace,commands=simulate(root,'candidate',completed,visited,True,500);item['start']=start;save(D/f'{start}-candidate-model-private.json',dict(summary=item,trace=trace,commands=commands));arms.append(item)
            if not item['pass_safety']:break
            gain=cache525['model_finish_episode_s']-item['model_finish_episode_s'];direct=(cache528 if start=='cold' else comparison_carry)['model_finish_episode_s']-item['model_finish_episode_s']
            if start=='cold':cold_gain=gain;direct_cold_gain=direct
            else:carry_gain=gain;direct_carry_gain=direct
    eligible=probe_pass and len(arms)==2 and all(x['pass_safety'] and x['high_fraction']>=.5 for x in arms) and cold_gain>=.50 and carry_gain>=.50 and direct_cold_gain>=.10 and direct_carry_gain>=0
    out=dict(status='PATH_MODEL_NATIVE_ELIGIBLE' if eligible else 'PATH_MODEL_NOT_PROMOTED',native_pair_eligible=eligible,probe_pass=probe_pass,probes=probes,arms=arms,comparison528_carry=comparison_carry,gain_vs525_cold_s=cold_gain,gain_vs525_carry_s=carry_gain,path_gain_vs528_cold_s=direct_cold_gain,path_gain_vs528_carry_s=direct_carry_gain,model_integrator_ticks=counter[0],source_wheel_force_evaluations_in_integrator=4*counter[0],explicit_force_evaluations=cost['force_evaluations'],planner_cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,native_resets=0,native_worlds=0,research_remaining=24155,reserve=84000,reserve_used=0,scope='Onlypathgenerationvs528fixedtop80controller. Nativewouldbe525vs530package;nofictitiousactual528/feasiblebound/11sclaim.')
    guard();save(G/'retry/line530_model_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':run()
