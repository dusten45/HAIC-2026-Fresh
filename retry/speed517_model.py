"""Extended fixed-budget qualification, cold and actual carry-state models."""
import datetime,hashlib,io,json,math,signal,time,unittest
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.speed517_control import path_for,markers,force_rows
from retry.corner515_control import project,reference,nominal,steering
from retry.corner515_model import margin
from retry.plan513_model import load_root
from retry.plan512_control import tick
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response517-private')

def run():
    t=time.perf_counter();cpu=time.process_time();counter=[0];force_evals=0;c=json.loads((G/'retry/speed517_contract.json').read_text())
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_MODEL_RETRY')
    def save(path,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode();files=list(D.iterdir())
        if len(files)>=4096 or sum(z.stat().st_size for z in files)+len(data)>96*1024**2:raise RuntimeError('PRIVATE_CAP')
        with path.open('xb') as f:f.write(data)
        path.chmod(0o600 if D in path.parents else 0o644)
    def guard(*a):
        if time.process_time()-cpu>=180 or time.perf_counter()-t>=240:raise RuntimeError('MODEL_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in c['source_sha256'].items())
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_IN_MODEL')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=Car.__init__=poison
    stream=io.StringIO();test=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('retry.test_speed517'));save(D/'model-pure-tests.json',dict(passed=test.wasSuccessful(),output=stream.getvalue(),model_integrator_ticks=0))
    if not test.wasSuccessful():raise RuntimeError('PURE_GATE')
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());initial=load_root(static['root']);paths={str(b):path_for(static,b) for b in (80.,100.)};roads=static['roads'];index=bounds(roads);edge=static['boundary'];ei=boundary_index(edge)
    native=json.loads(Path('/workspace/haic-response516-private/native-full-records-private.json').read_text());carry={}
    for a in native:
        label=str(int(a['budget']));x=json.loads(Path('/workspace/haic-response516-private/action-'+label+'-%03d.json'%a['actions']).read_text())['after_root_without_roads'];x['roads']=static['root']['roads'];carry[a['budget']]=(load_root(x),a['actions'])
    save(D/'frozen-paths-private.json',paths);save(D/'carry-inputs-private.json',{str(b):asdict(carry[b][0]) for b in carry});save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/speed517_contract.json').read_bytes()).hexdigest()))
    results=[]
    for start in ('cold','actual_carry'):
        for budget in (80.,100.):
            root,completed=(initial,0) if start=='cold' else carry[budget];path=paths[str(budget)];trace=[];events={};elapsed=0.;actions=0;stop='MAX300';minimum=margin(root,roads,index,edge,ei,static['obstacles']);overspeed=lateral=peak=0.;samples=clipped=0;prefix_exact=True
            previous=json.loads(Path('/workspace/haic-response516-private/exact_reset-'+str(int(budget))+'-model-private.json').read_text())['trace'] if start=='cold' else None
            for i in range(completed,300):
                guard()
                if minimum<.5:stop='MODEL_MARGIN';break
                action=np.array([steering(root,path),.32,0.],np.float32) if i<24 else nominal(root,path)[0];actions+=1;root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
                projection_bad=False
                for k in range(4):
                    before=root;force=force_rows(root,action);force_evals+=4;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);elapsed+=.02
                    q0,q=project(before.center,path),project(root.center,path);delta=q['s']-q0['s']
                    if delta<-.5 or delta>max(5.,2*math.dist(root.center,before.center)):projection_bad=True
                    speed=math.hypot(*root.planar.linear.velocity);v0=math.hypot(*before.planar.linear.velocity);target,ff=reference(q['s'],path);gap=margin(root,roads,index,edge,ei,static['obstacles']);minimum=min(minimum,gap);lateral=max(lateral,q['distance'])
                    if q['s']>=path['measurement_begin']:
                        overspeed=max(overspeed,speed-target);peak=max(peak,max(x['ratio'] for x in force));samples+=4;clipped+=sum(x['clipped'] for x in force)
                    for name,s in markers(path):
                        if name not in events and q0['s']<s<=q['s']:
                            f=(s-q0['s'])/(q['s']-q0['s']);events[name]=dict(lower=elapsed-.02,upper=elapsed,time=elapsed-.02+.02*f,speed=v0+f*(speed-v0),path_error_raw_post=q['distance'],yaw_raw_post=root.planar.yaw,heading_error_raw_post=math.remainder(root.planar.angle+math.pi/2-math.atan2(q['tangent'][1],q['tangent'][0]),2*math.pi))
                    state=asdict(root);state.pop('roads');record=dict(index=i+1,raw=k+1,root_without_roads=state,action=action.tolist(),station=q['s'],margin=gap,target=target,forces=force)
                    if previous is not None and len(trace)<len(previous):
                        old=previous[len(trace)];prefix_exact &= old['root_without_roads']==json.loads(json.dumps(state)) and old['action']==record['action']
                    trace.append(record)
                if projection_bad:stop='MODEL_PROJECTION_VALIDITY';break
                if minimum<.5:stop='MODEL_MARGIN';break
                if overspeed>5 or lateral>3 or peak>1.25 or (samples and clipped/samples>.10):stop='MODEL_DYNAMICS_GUARD';break
                if 'end'in events:stop='MODEL_WINDOW_END';break
            if previous is not None and len(trace)<len(previous):prefix_exact=False
            def duration(begin):return events['end']['time']-events[begin]['time'] if 'end'in events and begin in events else None
            passed=stop=='MODEL_WINDOW_END' and minimum>=.5 and overspeed<=5 and lateral<=3 and peak<=1.25 and (not samples or clipped/samples<=.10) and prefix_exact
            item=dict(start=start,budget=budget,stop=stop,actions=actions,raw_ticks=len(trace),min_margin_m=minimum,max_path_error_m=lateral,max_tracking_overspeed_m_s=overspeed,peak_force_ratio=peak,clipped_wheel_samples=clipped,wheel_samples=samples,previous516_model_prefix_exact=prefix_exact if start=='cold' else None,events=events,whole_window_time_s=duration('begin') if start=='cold' else None,next_window_time_s=duration('next_approach'),pass_gate=passed)
            save(D/(start+'-'+str(int(budget))+'-model-private.json'),dict(summary=item,trace=trace));results.append(item)
    comparisons=[]
    for start in ('cold','actual_carry'):
        b=next(x for x in results if x['start']==start and x['budget']==80);a=next(x for x in results if x['start']==start and x['budget']==100)
        whole=b['whole_window_time_s']-a['whole_window_time_s'] if start=='cold' and b['pass_gate'] and a['pass_gate'] else None
        nextgain=b['next_window_time_s']-a['next_window_time_s'] if b['pass_gate'] and a['pass_gate'] else None
        comparisons.append(dict(start=start,whole_extended_window_gain_s=whole,next_window_gain_s=nextgain,information_gate=bool(nextgain is not None and nextgain>=0 and (start!='cold' or whole>=.08))))
    eligible=all(x['pass_gate'] for x in results) and all(x['information_gate'] for x in comparisons)
    result=dict(status='EXTENSION_MODEL_NATIVE_ELIGIBLE' if eligible else 'EXTENSION_MODEL_NO_NATIVE',native_pair_eligible=eligible,arms=results,comparisons=comparisons,model_integrator_ticks=counter[0],model_wheel_force_evaluations=force_evals,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,native_actions=0,native_resets=0,native_worlds=0,research_remaining=25686,reserve=84000,reserve_used=0,scope='Whole extended spatialwindow and separate next approach window; cold whole gain not constructed by adding516 gain. Actualcarry starts differ, compared only through common nextwindow events.')
    guard();save(G/'retry/speed517_model_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
