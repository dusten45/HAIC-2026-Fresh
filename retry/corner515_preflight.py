"""Four saved-state curve rollouts, then conditional native eligibility only."""
import datetime,hashlib,io,json,math,signal,time,unittest
from pathlib import Path
from dataclasses import asdict,replace
import numpy as np
from retry.corner515_control import make_path,project,reference,future_floor,command,steering,hold
from retry.corner515_model import margin
from retry.plan513_model import load_root
from retry.plan512_control import tick
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response515-private')

def run():
    started=time.perf_counter();cpu=time.process_time();counter=[0];c=json.loads((G/'retry/corner515_model_contract.json').read_text())
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_MODEL_SCIENTIFIC_RETRY')
    def save(path,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode();files=list(D.iterdir())
        if len(files)>=3000 or sum(p.stat().st_size for p in files)+len(data)>64*1024**2:raise RuntimeError('STORAGE_CAP')
        with path.open('xb') as f:f.write(data)
        path.chmod(0o600 if D in path.parents else 0o644)
    def guard(*a):
        if time.process_time()-cpu>=180 or time.perf_counter()-started>=240:raise RuntimeError('MODEL_RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in c['source_sha256'].items())
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_IN_MODEL')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=Car.__init__=poison
    import retry.brake504_planar as p504
    import retry.brake508_corridor as p508
    import retry.plan512_control as p512
    original=p504.step;pure=[0]
    def counted(*a,**kw):pure[0]+=1;return original(*a,**kw)
    p504.step=p508.step=p512.step=counted
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('retry.test_corner515'))
    p504.step=p508.step=p512.step=original
    save(D/'model-pure-tests.json',dict(passed=tests.wasSuccessful(),output=stream.getvalue(),model_ticks=pure[0]))
    if not tests.wasSuccessful():raise RuntimeError('PURE_GATE')
    counter[0]=pure[0]
    static=json.loads((D/'collected-map-state-private.json').read_text());initial=load_root(static['root']);trigger=load_root(json.loads(Path('/workspace/haic-response512-private/trigger-scalar-private.json').read_text())['root'])
    path=make_path(static['boundary'],initial.center,static['obstacles']);roads=static['roads'];index=bounds(roads);edge=static['boundary'];ei=boundary_index(edge)
    save(D/'frozen-curve-reference-private.json',path);save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/corner515_model_contract.json').read_bytes()).hexdigest()))
    results=[]
    for startname,startroot,completed in [('exact_reset',initial,0),('observed_trigger_stress',trigger,24)]:
        for arm in ('reference','release'):
            root=startroot;trace=[];stop='MAX160';minimum=margin(root,roads,index,edge,ei,static['obstacles']);events={};below=0.;changed=0;first_release=None;seen_brake=False;tracking_max=0.;elapsed=0.;actions=0
            for i in range(completed,160):
                guard()
                if minimum<.5:stop='MODEL_MARGIN';break
                q=project(root.center,path)
                if i<24:action=np.array([steering(root,path),.32,0.],np.float32);details=dict(brake_changed=False)
                else:action,details=command(root,path,arm,counter)
                if details['brake_changed']:changed+=1
                if action[2]>0:seen_brake=True
                if seen_brake and action[2]==0 and first_release is None:first_release=q['s']
                actions+=1
                root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
                for k in range(4):
                    previous=root;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);elapsed+=.02
                    oldq,newq=project(previous.center,path),project(root.center,path);speed=math.hypot(*root.planar.linear.velocity);v0=math.hypot(*previous.planar.linear.velocity)
                    gap=margin(root,roads,index,edge,ei,static['obstacles']);minimum=min(minimum,gap);target,ff=reference(newq['s'],path);floor=future_floor(newq['s'],path)
                    if newq['s']>=path['measurement_begin']:tracking_max=max(tracking_max,speed-target)
                    in_window=path['measurement_begin']<=newq['s']<=path['measurement_end']
                    if in_window and action[2]>0 and speed<floor-.5:below+=.02
                    for name,station in [('begin',path['measurement_begin']),('corner_exit',path['corner_end']),('end',path['measurement_end'])]:
                        if name not in events and oldq['s']<station<=newq['s']:
                            f=(station-oldq['s'])/(newq['s']-oldq['s']);events[name]=dict(lower=elapsed-.02,upper=elapsed,time=elapsed-.02+.02*f,speed=v0+f*(speed-v0))
                    if 'corner_exit' in events and 'recovery50' not in events and v0<50<=speed:
                        f=(50-v0)/(speed-v0);events['recovery50']=dict(lower=elapsed-.02,upper=elapsed,time=elapsed-.02+.02*f,speed=50.)
                    state=asdict(root);state.pop('roads');trace.append(dict(index=i+1,raw=k+1,root_without_roads=state,action=action.tolist(),station=newq['s'],margin=gap,target=target,floor=floor,brake_changed=details['brake_changed']))
                if minimum<.5:stop='MODEL_MARGIN';break
                if tracking_max>5.:stop='MODEL_TRACKING_OVERSPEED';break
                if 'end' in events:stop='MODEL_WINDOW_END';break
            result=dict(start=startname,arm=arm,stop=stop,actions=actions,raw_ticks=len(trace),min_margin_m=minimum,max_tracking_overspeed_m_s=tracking_max,changed_brake_actions=changed,below_future_floor_braking_s=below,first_brake_release_station=first_release,events=events,
                window_time_s=events['end']['time']-events['begin']['time'] if 'end' in events and 'begin' in events else None,
                recovery50_after_exit_s=events['recovery50']['time']-events['corner_exit']['time'] if 'recovery50' in events else None,
                pass_gate=stop=='MODEL_WINDOW_END' and minimum>=.5 and tracking_max<=5.)
            save(D/(startname+'-'+arm+'-model-private.json'),dict(summary=result,trace=trace));results.append(result)
    safe=all(x['pass_gate'] for x in results);comparisons=[]
    for name in ('exact_reset','observed_trigger_stress'):
        b=next(x for x in results if x['start']==name and x['arm']=='reference');a=next(x for x in results if x['start']==name and x['arm']=='release')
        gain=b['window_time_s']-a['window_time_s'] if a['pass_gate'] and b['pass_gate'] else None
        recovery_gain=b['recovery50_after_exit_s']-a['recovery50_after_exit_s'] if a['recovery50_after_exit_s'] is not None and b['recovery50_after_exit_s'] is not None else None
        comparisons.append(dict(start=name,different_brake_decisions=a['changed_brake_actions'],window_time_gain_s=gain,recovery50_gain_s=recovery_gain,below_floor_braking_reduction_s=b['below_future_floor_braking_s']-a['below_future_floor_braking_s'],information_gate=bool(a['changed_brake_actions']>=1 and gain is not None and (gain>=.08 or (gain>=0 and recovery_gain is not None and recovery_gain>=.08)))))
    eligible=safe and all(x['information_gate'] for x in comparisons)
    collection=json.loads((G/'retry/corner515_collection_result.json').read_text())
    result=dict(status='CURVE_MODEL_NATIVE_ELIGIBLE' if eligible else 'CURVE_MODEL_NO_NATIVE',safety_pass=safe,native_pair_eligible=eligible,arms=results,comparisons=comparisons,model_ticks_including_pure_fixtures=counter[0],pure_fixture_model_ticks=pure[0],CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-started,
        native_counts_so_far=collection['counts'],research_remaining=25804,reserve=84000,reserve_used=0,scope='Current DEV first actual curve and obstacle-avoiding path, fixed finite model screen. Curve prediction not yet native-qualified; no lap record or old499 condition equivalence.')
    guard();save(G/'retry/corner515_model_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
