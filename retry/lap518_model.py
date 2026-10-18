"""Full closed-track finite model qualification, source-style finish estimate only."""
import datetime,hashlib,io,json,math,signal,time,unittest
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.lap518_control import path_for,project,nominal,steering,reference,force_rows
from retry.lap518_finish import hull_pose,tracker_for
from retry.corner515_model import margin
from retry.plan513_model import load_root
from retry.plan512_control import tick
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response518-private')

def run():
    t=time.perf_counter();cpu=time.process_time();counter=[0];force_evals=0;c=json.loads((G/'retry/lap518_contract.json').read_text())
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_SCIENTIFIC_MODEL_RETRY')
    def save(path,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode();files=list(D.iterdir())
        if len(files)>=8192 or sum(z.stat().st_size for z in files)+len(data)>128*1024**2:raise RuntimeError('PRIVATE_CAP')
        with path.open('xb') as f:f.write(data)
        path.chmod(0o600 if D in path.parents else 0o644)
    def guard(*a):
        if time.process_time()-cpu>=180 or time.perf_counter()-t>=240:raise RuntimeError('MODEL_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in c['source_sha256'].items())
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    for n,h in json.loads((D/'input-manifest-private.json').read_text()).items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_IN_MODEL')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=Car.__init__=poison
    stream=io.StringIO();test=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('retry.test_lap518'));save(D/'model-pure-tests.json',dict(passed=test.wasSuccessful(),output=stream.getvalue(),integrator_ticks=0))
    if not test.wasSuccessful():raise RuntimeError('PURE_GATE')
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());ledger=json.loads((D/'visited-current-ledger-private.json').read_text());initial=load_root(static['root']);paths={str(b):path_for(static,b) for b in (80.,100.)};roads=static['roads'];index=bounds(roads);edge=static['boundary'];ei=boundary_index(edge)
    old=json.loads(Path('/workspace/haic-response517-private/frozen-paths-private.json').read_text())['80.0'];closed=paths['80.0']
    changes=dict(max_existing150_point_displacement_m=max(math.dist(a,b) for a,b in zip(old['points'],closed['points'][:150])),max_existing150_arc_change_m=max(abs(a-b) for a,b in zip(old['arcs'][:150],closed['arcs'][:150])),max_80_existing150_speed_change_m_s=max(abs(a-math.sqrt(b)) for a,b in zip(old['speeds'],closed['launch_squared'][:150])),seam_point_distance_m=math.dist(closed['points'][-1],closed['points'][0]),path_length_m=closed['length'],obstacle_count=closed['obstacle_association_count'])
    save(D/'frozen-paths-private.json',paths);save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/lap518_contract.json').read_bytes()).hexdigest()))
    results=[];cold_safe=True
    for start in ('cold','actual_carry'):
        if start=='actual_carry' and not cold_safe:break
        for budget in (80.,100.):
            path=paths[str(budget)]
            if start=='cold':root=initial;completed=0;visited=set(ledger['initial_visited']);base_elapsed=0.;progress=project(root.center,path)['s']
            else:
                entry=ledger['carry'][str(int(budget))];x=json.loads(Path(entry['checkpoint']).read_text())['after_root_without_roads'];x['roads']=static['root']['roads'];root=load_root(x);completed=entry['completed_actions'];visited=set(entry['visited']);base_elapsed=completed*.08;progress=project(root.center,path,entry['prior_reference_end_anchor'])['s']
            tracker=tracker_for(static,root,visited,start=='actual_carry',1.02+base_elapsed);trace=[];elapsed=0.;stop='MAX500';actions=0;minimum=margin(root,roads,index,edge,ei,static['obstacles']);lateral=over=0.;force_stats={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')};arc_cross=None;projection_bad=False
            for i in range(completed,500):
                guard()
                if minimum<.5:stop='MODEL_MARGIN';break
                action=np.array([steering(root,path,progress),.32,0.],np.float32) if i<24 else nominal(root,path,progress);actions+=1;root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
                for k in range(4):
                    before=root;previous=progress;force=force_rows(root,action);force_evals+=4;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);elapsed+=.02;q=project(root.center,path,previous);progress=q['s'];delta=progress-previous
                    if delta<-.5 or delta>max(5.,2*math.dist(root.center,before.center)):projection_bad=True
                    gap=margin(root,roads,index,edge,ei,static['obstacles']);minimum=min(minimum,gap);lateral=max(lateral,q['distance']);speed=math.hypot(*root.planar.linear.velocity);target,ff=reference(progress,path);over=max(over,speed-target)
                    group='launch' if i<24 else 'running';z=force_stats[group];z['peak']=max(z['peak'],max(x['ratio'] for x in force));z['samples']+=4;z['clipped']+=sum(x['clipped'] for x in force)
                    for ids in root.current_contacts:visited.update(ids)
                    position,velocity=hull_pose(root);tracker.update(position,velocity,len(visited)/len(static['track']),1.02+base_elapsed+elapsed)
                    if arc_cross is None and previous<path['length']<=progress:arc_cross=base_elapsed+elapsed
                    state=asdict(root);state.pop('roads');trace.append(dict(index=i+1,raw=k+1,root_without_roads=state,action=action.tolist(),progress=progress,path_error=q['distance'],margin=gap,target=target,forces=force,visited_count=len(visited),finish_tracker=asdict(tracker)))
                    if tracker.finish_time_s is not None:stop='MODEL_SOURCE_STYLE_FINISH';break
                    if 50+4*completed+len(trace)>=c['TimeLimit_max_episode_steps']:stop='MODEL_TIME_LIMIT';break
                if stop in ('MODEL_SOURCE_STYLE_FINISH','MODEL_TIME_LIMIT'):break
                launch=force_stats['launch'];running=force_stats['running']
                if projection_bad:stop='MODEL_PROJECTION_VALIDITY';break
                if minimum<.5:stop='MODEL_MARGIN';break
                if lateral>3 or over>5 or launch['peak']>2.5 or (i>=23 and launch['samples'] and launch['clipped']/launch['samples']>.15) or running['peak']>1.25 or (running['samples'] and running['clipped']/running['samples']>.10):stop='MODEL_DYNAMICS_GUARD';break
                if progress>path['length']+10:stop='MODEL_NO_SOURCE_STYLE_FINISH_AFTER_ARC';break
            launch=force_stats['launch'];running=force_stats['running'];passed=stop=='MODEL_SOURCE_STYLE_FINISH' and minimum>=.5 and lateral<=3 and over<=5 and not projection_bad and launch['peak']<=2.5 and (not launch['samples'] or launch['clipped']/launch['samples']<=.15) and running['peak']<=1.25 and (not running['samples'] or running['clipped']/running['samples']<=.10)
            item=dict(start=start,budget=budget,stop=stop,actions=actions,raw_ticks=len(trace),model_finish_episode_s=tracker.finish_time_s-1.02 if tracker.finish_time_s is not None else None,model_finish_confirmation_episode_s=base_elapsed+elapsed if tracker.finish_time_s is not None else None,reference_arc_cross_episode_s=arc_cross,unwrapped_progress_end=progress,reference_laps=max(0,int(max(0.,progress)//path['length'])),visited_tiles=len(visited),tile_count=len(static['track']),min_margin_m=minimum,max_path_error_m=lateral,max_reference_overspeed_m_s=over,force_groups=force_stats,pass_gate=passed)
            save(D/(start+'-'+str(int(budget))+'-model-private.json'),dict(summary=item,trace=trace));results.append(item)
        if start=='cold':cold_safe=all(x['pass_gate'] for x in results) and len(results)==2
    cold=[x for x in results if x['start']=='cold'];gain=cold[0]['model_finish_episode_s']-cold[1]['model_finish_episode_s'] if all(x['pass_gate'] for x in cold) else None
    eligible=len(results)==4 and all(x['pass_gate'] for x in results) and gain is not None and gain>=.08
    result=dict(status='FULL_MODEL_NATIVE_ELIGIBLE' if eligible else 'FULL_MODEL_NO_NATIVE',native_pair_eligible=eligible,arms=results,cold_model_finish_gain_s=gain,path_changes=changes,model_integrator_ticks=counter[0],model_wheel_force_evaluations=force_evals,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,native_actions=0,native_resets=0,native_worlds=0,research_remaining=25472,reserve=84000,reserve_used=0,scope='Model source tracker on predicted hull/contacts/visited ledger is an estimate. Only actual native finish may establish lap performance. Full closed reference differs from finite517prefix as reported.')
    assert force_evals<=60000;guard();save(G/'retry/lap518_model_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
