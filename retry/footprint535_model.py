"""535geometry-admitted fixed-steering pedal hypothesis, bounded stage gates."""
import datetime,hashlib,json,math,signal,time
from collections import Counter
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.footprint535_control import choose,certifier,geometry_context
from retry.response528_control import choose as old_choose
from retry.frozen534_projection import initial_progress
from retry.drive519_control import project,steering,reference,force_rows,nominal
from retry.closure524_control import tick
from retry.plan513_model import load_root
from retry.lap518_finish import hull_pose,tracker_for
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response535-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();counter=[0];cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0);c=json.loads((G/'retry/footprint535_contract.json').read_text())
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_MODEL_RETRY')
    def save(p,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode()
        if len(list(D.iterdir()))>=8192 or sum(z.stat().st_size for z in D.iterdir())+len(data)>256*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def guard():
        if time.process_time()-cpu>=600 or time.perf_counter()-wall>=720:raise RuntimeError('MODEL_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
        if cost['force_evaluations']>600000 or counter[0]>120000:raise RuntimeError('MODEL_WORK_CAP')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,600)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,720)
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_IN_MODEL')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=Car.__init__=poison
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());ledger=json.loads(Path('/workspace/haic-response519-private/model-ledger-private.json').read_text());index=bounds(static['roads']);ei=boundary_index(static['boundary']);geometry=geometry_context(static)
    assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==c['fixed_path_sha256']
    save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/footprint535_contract.json').read_bytes()).hexdigest()))
    def root_from(p):
        x=json.loads(Path(p).read_text())['before_root_without_roads'];x['roads']=static['root']['roads'];return load_root(x)
    def simulate(root,variant,completed,visited,full,limit,case=None):
        path=paths[variant];s=initial_progress(root,path,completed);tracker=tracker_for(static,root,visited,completed>0,1.02+.08*completed) if full else None;elapsed=0.;trace=[];commands=[];minimum=margin(root,static['roads'],index,static['boundary'],ei,static['obstacles']);maxpath=maxover=maxspeed=maxbody=0.;stats={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')};modes={};failure=None;stop='PROBE_COMPLETE' if not full else 'MAX500'
        prefix=dict(clipped=case['history']['clipped'],samples=case['history']['samples']) if case else dict(clipped=0,samples=352 if completed else 0)
        stats['running']['clipped']=prefix['clipped'];stats['running']['samples']=prefix['samples']
        for i in range(completed,min(500,completed+limit)):
            guard()
            if cost['force_evaluations']+6200>600000:raise RuntimeError('FORCE_CAP_RESERVE')
            if i<24:action=np.array([steering(root,path,s),.32,0],np.float32);detail=dict(mode='FIXED_LAUNCH')
            else:
                if variant=='baseline':action,detail=old_choose(root,path,paths['baseline_backup'],s,counter,cost,history=(stats['running']['clipped'],stats['running']['samples']))
                else:action,detail=choose(root,path,paths['backup'],s,counter,cost,history=(stats['running']['clipped'],stats['running']['samples']),geometry=geometry)
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
    # Diagnostic roots are fixedbefore535outcome, all from534executedpast.
    cases=json.loads((D/'late-roots-private.json').read_text());diagnostics=[];early_case=None;early_possible=False
    for case in cases:
        guard();state=dict(case['root_without_roads']);state['roads']=static['root']['roads'];root=load_root(state);s=initial_progress(root,paths['candidate'],case['index']-1);history=(case['history']['clipped'],case['history']['samples']);old_action,old_detail=old_choose(root,paths['candidate'],paths['backup'],s,counter,cost,history=history);new_action,new_detail=choose(root,paths['candidate'],paths['backup'],s,counter,cost,history=history,geometry=geometry);cert=certifier(root,paths['candidate'],paths['backup'],s,counter,cost,geometry,history=history);old_geo=cert(old_action) if old_action is not None else None
        grid=[]
        if new_action is None:
            lock=np.float32(.9)
            if float(lock)<.9:lock=np.nextafter(lock,np.float32(1.))
            values=sorted(set([float(np.float32(-1+i/4)) for i in range(9)]+[-float(lock),-float(np.nextafter(lock,np.float32(0.)))]))
            steer=float(nominal(root,paths['candidate'],s)[0])
            for u in values:
                guard();action=np.array([steer,max(0.,u),max(0.,-u)],np.float32);report=cert(action);grid.append(dict(u=u,report=report))
        reports=new_detail.get('trials',new_detail.get('reports',[]));footprints=[x['first_footprint_violation'] for x in reports if x.get('first_footprint_violation')];record=dict(index=case['index'],initial_margin_m=case['initial_margin_m'],old_mode=old_detail['mode'],new_mode=new_detail['mode'],new_safe_command=new_action is not None,fresh_final=new_detail.get('final_recertified',False),steering_identical=bool(new_action is None or old_action is None or new_action[0].tobytes()==old_action[0].tobytes()),old_action_geometry_certificate=old_geo,finite_new_trial_failure_reasons=dict(Counter(x['reason'] for x in reports if not x.get('ok'))),full_signed_grid_count=len(grid),full_signed_grid_safe_count=sum(x['report']['ok'] for x in grid),full_signed_grid_first_hold_safe_count=sum(x['report']['first_hold_pass'] for x in grid),full_signed_grid_failure_reasons=dict(Counter(x['report']['reason'] for x in grid if not x['report']['ok'])),earliest_failed_candidate_footprint_raw=min((x['raw_from_root'] for x in footprints),default=None))
        diagnostics.append(record);save(D/f"diagnostic-root-{case['index']}-private.json",dict(summary=record,new_detail=new_detail,old_detail=old_detail,grid=grid,new_action=None if new_action is None else new_action.tolist()))
        if case['index']==141:early_case=case;early_possible=new_action is not None
    early=None
    if early_possible:
        state=dict(early_case['root_without_roads']);state['roads']=static['root']['roads'];early,trace,commands=simulate(load_root(state),'candidate',early_case['index']-1,set(),False,36,early_case);save(D/'early-recovery-private.json',dict(summary=early,trace=trace,commands=commands))
    pilot_pass=bool(early and early['pass_safety'] and early['raw_ticks']==144);regressions=[];regression_pass=False
    if pilot_pass:
        for case in json.loads((D/'risks-private.json').read_text()):
            state=dict(case['root_without_roads']);state['roads']=static['root']['roads'];item,trace,commands=simulate(load_root(state),'candidate',case['index']-1,set(),False,24,case);regressions.append(dict(label=case['label'],**item));save(D/f"regression-{case['label']}-private.json",dict(summary=item,trace=trace,commands=commands))
            if not item['pass_safety']:break
        regression_pass=len(regressions)==2 and all(x['pass_safety'] and x['raw_ticks']==96 for x in regressions)
    arms=[];cold_gain=carry_gain=direct_cold_gain=direct_carry_gain=None;comparison_carry=None;cache528=json.loads(Path('/workspace/haic-response528-private/cold-candidate-model-private.json').read_text())['summary']
    if pilot_pass and regression_pass:
        for start in ('cold','carry'):
            if start=='carry' and (cold_gain is None or cold_gain<.50 or direct_cold_gain<.10 or not arms[-1]['pass_safety'] or arms[-1]['high_fraction']<.5):break
            cache525=json.loads(Path('/workspace/haic-response525-private/'+('cold-governor-B-model-private.json' if start=='cold' else 'carry-governor-B-model-private.json')).read_text())['summary']
            if start=='cold':root=load_root(static['root']);completed=0;visited=set(ledger['initial_visited'])
            else:
                root=root_from(ledger['checkpoint']);completed=ledger['completed_actions'];visited=set(ledger['carry_visited']);comparison_carry,trace,commands=simulate(root,'baseline',completed,set(visited),True,500);save(D/'carry-baseline528-model-private.json',dict(summary=comparison_carry,trace=trace,commands=commands))
                if not comparison_carry['pass_safety']:break
            item,trace,commands=simulate(root,'candidate',completed,visited,True,500);item['start']=start;arms.append(item);save(D/f'{start}-candidate-model-private.json',dict(summary=item,trace=trace,commands=commands))
            if not item['pass_safety']:break
            gain=cache525['model_finish_episode_s']-item['model_finish_episode_s'];direct=(cache528 if start=='cold' else comparison_carry)['model_finish_episode_s']-item['model_finish_episode_s']
            if start=='cold':cold_gain=gain;direct_cold_gain=direct
            else:carry_gain=gain;direct_carry_gain=direct
    eligible=pilot_pass and regression_pass and len(arms)==2 and all(x['pass_safety'] and x['high_fraction']>=.5 for x in arms) and cold_gain>=.50 and carry_gain>=.50 and direct_cold_gain>=.10 and direct_carry_gain>=.10
    out=dict(status='FOOTPRINT_MODEL_NATIVE_ELIGIBLE' if eligible else 'FOOTPRINT_MODEL_NOT_PROMOTED',native_pair_eligible=eligible,diagnostics=diagnostics,pilot_pass=pilot_pass,early_recovery=early,regression_pass=regression_pass,regressions=regressions,arms=arms,comparison528_carry=comparison_carry,gain_vs525_cold_s=cold_gain,gain_vs525_carry_s=carry_gain,package_gain_vs528_cold_s=direct_cold_gain,package_gain_vs528_carry_s=direct_carry_gain,model_integrator_ticks=counter[0],source_wheel_force_evaluations_in_integrator=4*counter[0],explicit_force_evaluations=cost['force_evaluations'],planner_cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,native_resets=0,native_worlds=0,research_remaining=24155,reserve=84000,reserve_used=0,scope='535onlywholefootprint>=.5in12holdandfreshfinalcertification;533path/steeringfixed. Finitepedalgrid/tailfailureisnotproofallpedalpoliciesimpossible.533unconvergedand534failurepreserved;noactual/pixel/11sclaim.')
    guard();save(G/'retry/footprint535_model_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':run()
