"""Saved DEV model screen only. 3 roots x 3 laws x 3 bounded perturb schedules."""
import datetime,hashlib,io,json,math,resource,signal,sys,time,unittest
from pathlib import Path
from dataclasses import asdict
import numpy as np
from retry.plan512_control import tick,station
from retry.plan513_control import steering,steered,response_action,scalar_action
from retry.plan513_model import load_root,margin
from retry.plan514_control import robust_action,perturb,PHYSICAL_LOW,PHYSICAL_HIGH,POSITION_ALLOWANCE,SPEED_ALLOWANCE
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response514-private')

def run():
    started=time.perf_counter();cpu=time.process_time();counter=[0]
    c=json.loads((G/'retry/plan514_contract.json').read_text())
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_SCIENTIFIC_MODEL_RETRY')
    def save(p,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode();files=list(D.iterdir())
        if len(files)>=256 or sum(z.stat().st_size for z in files)+len(data)>64*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def guard(*a):
        if time.process_time()-cpu>=180 or time.perf_counter()-started>=240:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in c['source_sha256'].items())
    for name,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h
    # Poison actual constructors/reset/step: this worker has no native permission.
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car as NativeCar
    def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
    for cls,names in [(CarRacing,('__init__','reset','step')),(NativeCar,('__init__',))]:
        for name in names:setattr(cls,name,poison)
    # Count EVERY pure fixture integrator call too, through its defining symbol
    # and the cached imports used by508/512. Test module imports occur afterward.
    import retry.brake504_planar as p504
    import retry.brake508_corridor as p508
    import retry.plan512_control as p512
    pure=[0];original_step=p504.step
    def counted(*a,**kw):pure[0]+=1;return original_step(*a,**kw)
    p504.step=p508.step=p512.step=counted
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('retry.test_plan514'))
    p504.step=p508.step=p512.step=original_step
    save(D/'pure-tests.json',dict(passed=tests.wasSuccessful(),output=stream.getvalue(),pure_fixture_model_ticks=pure[0]))
    if not tests.wasSuccessful():raise RuntimeError('PURE_GATE')
    counter[0]=pure[0]
    pref=json.loads((G/'retry/plan513_preflight_result.json').read_text())
    pos=max(x['max_position_error_m'] for x in pref['calibration']);vel=max(x['max_speed_error_m_s'] for x in pref['calibration'])
    assert POSITION_ALLOWANCE==math.ceil(8*pos/.001)*.001 and SPEED_ALLOWANCE==math.ceil(8*vel/.001)*.001
    initial=load_root(json.loads(Path('/workspace/haic-response513-private/initial-reconstructed-private.json').read_text())['root'])
    oldtrigger=json.loads(Path('/workspace/haic-response512-private/trigger-scalar-private.json').read_text());trigger=load_root(oldtrigger['root']);plan=oldtrigger['plan']
    stop=load_root(json.loads(Path('/workspace/haic-response513-private/plan-stop-response-private.json').read_text())['root'])
    mesh=json.loads(Path('/workspace/haic-response511-private/map-steady-private.json').read_text());roads=mesh['roads'];roadindex=bounds(roads);edge=mesh['boundary'];ei=boundary_index(edge)
    roots=[('reset_reconstructed',initial,0),('trigger_copied',trigger,24),('native_stop_copied',stop,35)]
    save(D/'frozen-inputs-private.json',dict(roots={name:asdict(root) for name,root,i in roots},plan=plan,sample_residual_maxima=dict(position_m=pos,speed_m_s=vel)))
    save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/plan514_contract.json').read_bytes()).hexdigest()))
    results=[]
    for rootname,startroot,completed in roots:
        for schedule in ('none','persistent_positive','alternating'):
            for arm in ('scalar','original','guarded'):
                guard();root=perturb(startroot,plan,0 if schedule=='none' else 1);trace=[];stopreason='HOLD_CAP';minimum=margin(root,roads,roadindex,edge,ei);cross=None;actions=0;firstbrake=None;empty=False
                for i in range(completed,200):
                    guard()
                    if minimum<.5:stopreason='MODEL_ROAD_MARGIN';break
                    steer=steering(root,plan);root=steered(root,[steer,0,0])
                    try:
                        if i<24:action=np.array([steer,.32,0],np.float32);details=None
                        else:
                            action,details=(scalar_action(root,steer,plan) if arm=='scalar' else response_action(root,steer,plan,counter) if arm=='original' else robust_action(root,steer,plan,counter))
                    except ValueError as e:stopreason='PLAN_STOP:'+str(e);empty='EMPTY' in str(e);break
                    assert action.dtype==np.float32 and -1<=action[0]<=1 and 0<=action[1]<=1 and 0<=action[2]<=np.float32(.3) and not(action[1]>0 and action[2]>0)
                    actions+=1
                    if action[2]>0 and firstbrake is None:firstbrake=i+1
                    for k in range(4):
                        previous=root;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter)
                        gap=margin(root,roads,roadindex,edge,ei);minimum=min(minimum,gap)
                        a,b=station(previous.center,plan),station(root.center,plan);speed=math.hypot(*root.planar.linear.velocity)
                        lower=(actions-1)*.08+k*.02
                        if cross is None and a<plan['gate']<=b:
                            f=(plan['gate']-a)/(b-a);v0=math.hypot(*previous.planar.linear.velocity)
                            cross=dict(time_lower_s=lower,time_upper_s=lower+.02,interpolated_time_s=lower+.02*f,speed_m_s=v0+f*(speed-v0),kind='raw_linear_interpolation')
                        state=asdict(root);state.pop('roads')
                        trace.append(dict(action=i+1,raw=k+1,root_without_static_roads=state,action_value=action.tolist(),margin=gap))
                    # Perturb at the completed wrapper boundary, same local-step
                    # schedule for all three laws. This is a state injection test,
                    # not a measured/native trajectory.
                    sign=0 if schedule=='none' else 1 if schedule=='persistent_positive' else (-1 if actions%2 else 1)
                    old_s=station(root.center,plan);root=perturb(root,plan,sign);minimum=min(minimum,margin(root,roads,roadindex,edge,ei))
                    if cross is None and old_s<plan['gate']<=station(root.center,plan):
                        cross=dict(time_lower_s=actions*.08,time_upper_s=actions*.08,interpolated_time_s=actions*.08,speed_m_s=math.hypot(*root.planar.linear.velocity),kind='artificial_boundary_shift')
                    if minimum<.5:stopreason='MODEL_ROAD_MARGIN';break
                    if cross is not None:stopreason='MODEL_GATE';break
                result=dict(root=rootname,schedule=schedule,arm=arm,stop=stopreason,actions=actions,raw_ticks=len(trace),min_margin_m=minimum,crossing=cross,
                    goal_pass=bool(stopreason=='MODEL_GATE' and PHYSICAL_LOW<=cross['speed_m_s']<=PHYSICAL_HIGH and minimum>=.5),planning_empty=empty,first_brake_global_action=firstbrake)
                save(D/(rootname+'-'+schedule+'-'+arm+'-private.json'),dict(summary=result,trace=trace));results.append(result)
    guarded=[x for x in results if x['arm']=='guarded'];repair_pass=all(x['goal_pass'] and not x['planning_empty'] for x in guarded)
    paired=[]
    for name,root,completed in roots[:2]:
        for schedule in ('none','persistent_positive','alternating'):
            b=next(x for x in results if x['root']==name and x['schedule']==schedule and x['arm']=='scalar')
            a=next(x for x in results if x['root']==name and x['schedule']==schedule and x['arm']=='guarded')
            paired.append(dict(root=name,schedule=schedule,both_goal_pass=b['goal_pass'] and a['goal_pass'],interpolated_gain_s=b['crossing']['interpolated_time_s']-a['crossing']['interpolated_time_s'] if b['goal_pass'] and a['goal_pass'] else None,
                certified_gain_lower_s=b['crossing']['time_lower_s']-a['crossing']['time_upper_s'] if b['goal_pass'] and a['goal_pass'] else None))
    time_pass=all(x['both_goal_pass'] and x['certified_gain_lower_s']>=.08 for x in paired)
    summary=dict(status='MODEL_REPAIR_AND_TIME_GATE_PASS' if repair_pass and time_pass else 'MODEL_REPAIR_ONLY_NO_TIME_EFFECT' if repair_pass else 'MODEL_REPAIR_NOT_ESTABLISHED',repair_pass=repair_pass,time_effect_gate=time_pass,
        results=results,comparable_time_results=paired,model_ticks_including_pure_fixtures=counter[0],pure_fixture_model_ticks=pure[0],CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-started,
        native_worlds=0,native_actions=0,native_resets=0,research_remaining=25804,reserve=84000,reserve_used=0,
        scope='Finite saved DEV model states and two-coordinate bounded injections; empirical allowances, no unobserved-state safety proof. Physical crossing band unchanged, no lap/finish/native gain claim. No native allowed regardless outcome.')
    guard();save(G/'retry/plan514_result.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':run()
