"""535geometry-admitted fixed-steering pedal hypothesis, bounded stage gates."""
import datetime,hashlib,json,math,signal,time,traceback
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
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response535-recovery-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();counter=[0];cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0);c=json.loads((G/'retry/footprint535_recovery_contract.json').read_text())
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
    save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/footprint535_recovery_contract.json').read_bytes()).hexdigest()))
    def root_from(p):
        x=json.loads(Path(p).read_text())['before_root_without_roads'];x['roads']=static['root']['roads'];return load_root(x)
    def simulate(root,variant,completed,visited,full,limit,case=None):
        path=paths[variant];s=initial_progress(root,path,completed);tracker=tracker_for(static,root,visited,completed>0,1.02+.08*completed) if full else None;elapsed=0.;trace=[];commands=[];minimum=margin(root,static['roads'],index,static['boundary'],ei,static['obstacles']);maxpath=maxover=maxspeed=maxbody=0.;stats={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')};modes={};failure=None;stop='PROBE_COMPLETE' if not full else 'MAX500'
        prefix=dict(clipped=case['history']['clipped'],samples=case['history']['samples']) if case else dict(clipped=0,samples=352 if completed else 0)
        stats['running']['clipped']=prefix['clipped'];stats['running']['samples']=prefix['samples']
        for i in range(completed,min(500,completed+limit)):
            guard()
            with (D/'latest-carry-cost-private.json').open('w') as f:json.dump(dict(next_action=i+1,model_ticks=counter[0],cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall),f)
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
    prior=Path('/workspace/haic-response535-private');cold=json.loads((prior/'cold-candidate-model-private.json').read_text())['summary'];basecarry=json.loads((prior/'carry-baseline528-model-private.json').read_text())['summary'];early=json.loads((prior/'early-recovery-private.json').read_text())['summary'];regressions=[json.loads((prior/f'regression-{x}-private.json').read_text())['summary'] for x in ('obstacle','curvature')];cache528=json.loads(Path('/workspace/haic-response528-private/cold-candidate-model-private.json').read_text())['summary'];cache525cold=json.loads(Path('/workspace/haic-response525-private/cold-governor-B-model-private.json').read_text())['summary'];cache525carry=json.loads(Path('/workspace/haic-response525-private/carry-governor-B-model-private.json').read_text())['summary'];assert early['pass_safety'] and early['raw_ticks']==144 and all(x['pass_safety'] and x['raw_ticks']==96 for x in regressions);assert cold['pass_safety'] and basecarry['pass_safety'];cold_gain=cache525cold['model_finish_episode_s']-cold['model_finish_episode_s'];direct_cold=cache528['model_finish_episode_s']-cold['model_finish_episode_s'];assert cold_gain>=.5 and direct_cold>=.1 and cold['high_fraction']>=.5
    error=None;carry=None;trace=[];commands=[]
    try:
        root=root_from(ledger['checkpoint']);carry,trace,commands=simulate(root,'candidate',ledger['completed_actions'],set(ledger['carry_visited']),True,500);save(D/'carry-candidate-model-private.json',dict(summary=carry,trace=trace,commands=commands))
    except BaseException as exc:
        error=type(exc).__name__+':'+str(exc);save(D/'carry-technical-error-private.json',dict(error=error,traceback=traceback.format_exc(),model_ticks=counter[0],cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
    gain=cache525carry['model_finish_episode_s']-carry['model_finish_episode_s'] if carry and carry['pass_safety'] else None;direct=basecarry['model_finish_episode_s']-carry['model_finish_episode_s'] if carry and carry['pass_safety'] else None;eligible=bool(carry and carry['pass_safety'] and gain>=.5 and direct>=.1 and carry['high_fraction']>=.5)
    out=dict(status='FOOTPRINT_MODEL_NATIVE_ELIGIBLE' if eligible else 'FOOTPRINT_RECOVERY_NOT_PROMOTED',native_pair_eligible=eligible,technical_recovery_only=True,controller_path_thresholds_unchanged=True,pilot_pass=True,regression_pass=True,cached_cold=cold,cached_528carry=basecarry,new_carry=carry,gain_vs525_cold_s=cold_gain,package_gain_vs528_cold_s=direct_cold,gain_vs525_carry_s=gain,package_gain_vs528_carry_s=direct,technical_error=error,model_integrator_ticks=counter[0],source_wheel_force_evaluations_in_integrator=4*counter[0],explicit_force_evaluations=cost['force_evaluations'],planner_cost=cost,prior535_partial_cost_counts_exact=False,prior535_budget_reserved_model_ticks=120000,prior535_budget_reserved_explicit_force_evaluations=600000,prior535_budget_reserved_geometry_checks=130000,prior535_CPU_cap_reached_s=600,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,native_resets=0,native_worlds=0,research_remaining=24155,reserve=84000,reserve_used=0,scope='Same535fixedcontroller/path. Reusecompletedearly/regression/cold/528carry;repeatonlyincompletecandidatecarryafterCPUstop. Priorpartialcarryneverfinish/gainclaim;countsboundedconservatively,notfabricatedexact.')
    save(G/'retry/footprint535_recovery_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':run()
