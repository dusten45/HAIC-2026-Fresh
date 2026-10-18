"""One frozen spline-path candidate; no native calls or fallback search."""
import datetime,hashlib,io,json,math,signal,time,unittest
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.drive519_control import path_for,project,nominal,steering,reference,force_rows
from retry.lap518_finish import hull_pose,tracker_for
from retry.corner515_model import margin
from retry.plan513_model import load_root
from retry.plan512_control import tick
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response521-private')

def run():
    t=time.perf_counter();cpu=time.process_time();counter=[0];force_evals=0;c=json.loads((G/'retry/study521_contract.json').read_text())
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_SCIENTIFIC_RETRY')
    def save(path,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode();files=list(D.iterdir())
        if len(files)>=512 or sum(z.stat().st_size for z in files)+len(data)>96*1024**2:raise RuntimeError('PRIVATE_CAP')
        with path.open('xb') as f:f.write(data)
        path.chmod(0o600 if D in path.parents else 0o644)
    def guard(*a):
        if time.process_time()-cpu>=180 or time.perf_counter()-t>=240:raise RuntimeError('MODEL_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    for n,h in c['model_source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=Car.__init__=poison
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('retry.test_path521'));save(D/'model-pure-tests.json',dict(passed=tests.wasSuccessful(),output=stream.getvalue(),model_integrator_ticks=0))
    if not tests.wasSuccessful():raise RuntimeError('PURE_GATE')
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());design=json.loads((G/'retry/study521_design.json').read_text());assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==design['frozen_paths_private_sha256']
    ledger=json.loads(Path('/workspace/haic-response519-private/model-ledger-private.json').read_text());roads=static['roads'];index=bounds(roads);edge=static['boundary'];ei=boundary_index(edge)
    old=json.loads(Path('/workspace/haic-response519-private/cold-source_drive-model-private.json').read_text())['summary'];assert old['pass_gate']
    results=[dict(old,start='cold',variant='baseline',reused_prior_model=True,reused_prior_model_integrator_ticks=old['raw_ticks'],new_model_integrator_ticks=0)]
    save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/study521_contract.json').read_bytes()).hexdigest()))
    for start,variants in [('cold',('spline',)),('same_actual_exit_state',('baseline','spline'))]:
        if not design['geometric_screen_pass']:break
        if start!='cold' and (not results[1]['pass_gate'] or old['model_finish_episode_s']-results[1]['model_finish_episode_s']<.5):break
        for variant in variants:
            path=paths[variant]
            if start=='cold':root=load_root(static['root']);completed=0;visited=set(ledger['initial_visited']);base=0.;progress=project(root.center,path)['s']
            else:
                x=json.loads(Path(ledger['checkpoint']).read_text())['before_root_without_roads'];x['roads']=static['root']['roads'];root=load_root(x);completed=ledger['completed_actions'];visited=set(ledger['carry_visited']);base=completed*.08;progress=project(root.center,path,ledger['anchor'])['s']
            tracker=tracker_for(static,root,visited,start!='cold',1.02+base);trace=[];elapsed=0.;actions=0;stop='MAX500';minimum=margin(root,roads,index,edge,ei,static['obstacles']);lateral=over=unused=0.;groups={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')};bad=False
            for i in range(completed,500):
                guard()
                if minimum<.5:stop='MODEL_MARGIN';break
                action=np.array([steering(root,path,progress),.32,0.],np.float32) if i<24 else nominal(root,path,progress);actions+=1;root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
                for k in range(4):
                    if counter[0]>=5000:raise RuntimeError('MODEL_TICK_CAP_521')
                    before=root;s0=progress;force=force_rows(root,action);force_evals+=4;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);elapsed+=.02;q=project(root.center,path,s0);progress=q['s'];bad |= progress-s0<-.5 or progress-s0>max(5.,2*math.dist(root.center,before.center));gap=margin(root,roads,index,edge,ei,static['obstacles']);minimum=min(minimum,gap);lateral=max(lateral,q['distance']);speed=math.hypot(*root.planar.linear.velocity);target,ff=reference(progress,path)
                    if i>=24:over=max(over,speed-target)
                    else:unused=max(unused,speed-target)
                    z=groups['launch' if i<24 else 'running'];z['peak']=max(z['peak'],max(x['ratio'] for x in force));z['samples']+=4;z['clipped']+=sum(x['clipped'] for x in force)
                    for ids in root.current_contacts:visited.update(ids)
                    pos,vel=hull_pose(root);tracker.update(pos,vel,len(visited)/len(static['track']),1.02+base+elapsed);state=asdict(root);state.pop('roads');trace.append(dict(index=i+1,raw=k+1,root_without_roads=state,progress=progress,path_error=q['distance'],margin=gap,target=target,action=action.tolist(),forces=force,visited_count=len(visited),finish_tracker=asdict(tracker)))
                    if tracker.finish_time_s is not None:stop='MODEL_SOURCE_STYLE_FINISH';break
                    if 50+4*completed+len(trace)>=c['TimeLimit_max_episode_steps']:stop='MODEL_TIME_LIMIT';break
                if stop in ('MODEL_SOURCE_STYLE_FINISH','MODEL_TIME_LIMIT'):break
                launch,running=groups['launch'],groups['running']
                if bad:stop='MODEL_PROJECTION';break
                if minimum<.5:stop='MODEL_MARGIN';break
                if lateral>3 or over>5 or launch['peak']>2.5 or (i>=23 and launch['samples'] and launch['clipped']/launch['samples']>.15) or running['peak']>1.25 or (running['samples'] and running['clipped']/running['samples']>.10):stop='MODEL_DYNAMICS';break
                if progress>path['length']+10:stop='MODEL_NO_FINISH_AFTER_ARC';break
            launch,running=groups['launch'],groups['running'];passed=stop=='MODEL_SOURCE_STYLE_FINISH' and minimum>=.5 and lateral<=3 and over<=5 and not bad and launch['peak']<=2.5 and (not launch['samples'] or launch['clipped']/launch['samples']<=.15) and running['peak']<=1.25 and (not running['samples'] or running['clipped']/running['samples']<=.10)
            item=dict(start=start,variant=variant,stop=stop,actions=actions,raw_ticks=len(trace),reused_prior_model=False,min_margin_m=minimum,max_path_error_m=lateral,max_reference_overspeed_m_s=over,max_unused_launch_reference_difference=unused,force_groups=groups,visited_tiles=len(visited),model_finish_episode_s=tracker.finish_time_s-1.02 if tracker.finish_time_s is not None else None,pass_gate=passed)
            save(D/(start+'-'+variant+'-model-private.json'),dict(summary=item,trace=trace));results.append(item)
    coldgain=old['model_finish_episode_s']-results[1]['model_finish_episode_s'] if len(results)>1 and results[1]['pass_gate'] else None;carrygain=None
    if len(results)==4 and results[2]['pass_gate'] and results[3]['pass_gate']:carrygain=results[2]['model_finish_episode_s']-results[3]['model_finish_episode_s']
    propose=len(results)==4 and all(x['pass_gate'] for x in results) and coldgain>=.5 and carrygain>=.5
    clocks={v:sum(2*d/(math.sqrt(p['launch_squared'][i])+math.sqrt(p['launch_squared'][i+1])) for i,d in enumerate(p['ds'])) for v,p in paths.items()}
    result=dict(status='MODEL_CANDIDATE_FOR_LATER_NATIVE' if propose else 'MODEL_CANDIDATE_NOT_PROMOTED',propose_later_native=propose,design_screen_pass=design['geometric_screen_pass'],arms=results,cold_finish_gain_s=coldgain,same_actual_exit_finish_gain_s=carrygain,descriptive_scalar_reference_clocks_s=clocks,clocks_are_not_feasible_or_optimal_bounds=True,new_model_integrator_ticks=counter[0],reused_prior_model_ticks_not_new=1020,new_model_wheel_force_evaluations=force_evals,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,native_actions=0,native_resets=0,native_worlds=0,research_remaining=24938,reserve=84000,reserve_used=0,scope='One spline-path change; same519 speed laws, steady pedals, gains, steering rule, launch. Geometry-induced profile changes are reported, no separate cap tuning. No native permitted.')
    assert force_evals<=20000;guard();save(G/'retry/study521_model_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
