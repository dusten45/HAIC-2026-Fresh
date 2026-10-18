"""Finite own-state curve models; rejects unsafe or low-information native runs."""
import datetime,hashlib,io,json,math,signal,time,unittest
from pathlib import Path
from dataclasses import asdict,replace
import numpy as np
from retry.speed516_control import path_for,force_rows
from retry.corner515_control import project,reference,nominal,steering,future_floor
from retry.corner515_model import margin
from retry.plan513_model import load_root
from retry.plan512_control import tick
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response516-private')

def run():
    t=time.perf_counter();cpu=time.process_time();counter=[0];force_evals=0;c=json.loads((G/'retry/speed516_contract.json').read_text())
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_MODEL_SCIENTIFIC_RETRY')
    def save(path,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode();files=list(D.iterdir())
        if len(files)>=3000 or sum(p.stat().st_size for p in files)+len(data)>64*1024**2:raise RuntimeError('PRIVATE_CAP')
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
    stream=io.StringIO();test=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('retry.test_speed516'))
    save(D/'model-pure-tests.json',dict(passed=test.wasSuccessful(),output=stream.getvalue(),integrator_ticks=0))
    if not test.wasSuccessful():raise RuntimeError('PURE_GATE')
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());initial=load_root(static['root']);trigger=load_root(json.loads(Path('/workspace/haic-response512-private/trigger-scalar-private.json').read_text())['root'])
    roads=static['roads'];index=bounds(roads);edge=static['boundary'];ei=boundary_index(edge);results=[]
    paths={str(b):path_for(static,b) for b in (80.,100.)};save(D/'frozen-paths-private.json',paths)
    save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/speed516_contract.json').read_bytes()).hexdigest()))
    for label,startroot,completed in [('exact_reset',initial,0),('trigger_stress',trigger,24)]:
        for budget in (80.,100.):
            root=startroot;path=paths[str(budget)];trace=[];events={};stop='MAX160';elapsed=0.;actions=0;minimum=margin(root,roads,index,edge,ei,static['obstacles']);overspeed=0.;lateral=0.;peak=0.;samples=clipped=0;replay_exact=True
            old=json.loads(Path('/workspace/haic-response515-private/'+('exact_reset' if label=='exact_reset' else 'observed_trigger_stress')+'-reference-model-private.json').read_text())['trace'] if budget==80. else None
            for i in range(completed,160):
                guard()
                if minimum<.5:stop='MODEL_MARGIN';break
                action=np.array([steering(root,path),.32,0.],np.float32) if i<24 else nominal(root,path)[0]
                actions+=1;root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
                for k in range(4):
                    before=root;force=force_rows(root,action);force_evals+=4;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);elapsed+=.02
                    q0,q=project(before.center,path),project(root.center,path);speed=math.hypot(*root.planar.linear.velocity);v0=math.hypot(*before.planar.linear.velocity);target,ff=reference(q['s'],path)
                    gap=margin(root,roads,index,edge,ei,static['obstacles']);minimum=min(minimum,gap);lateral=max(lateral,q['distance'])
                    if q['s']>=path['measurement_begin']:
                        overspeed=max(overspeed,speed-target);peak=max(peak,max(x['ratio'] for x in force));samples+=4;clipped+=sum(x['clipped'] for x in force)
                    for name,s in [('begin',path['measurement_begin']),('corner_exit',path['corner_end']),('end',path['measurement_end'])]:
                        if name not in events and q0['s']<s<=q['s']:
                            f=(s-q0['s'])/(q['s']-q0['s']);events[name]=dict(lower=elapsed-.02,upper=elapsed,time=elapsed-.02+.02*f,speed=v0+f*(speed-v0))
                    state=asdict(root);state.pop('roads');record=dict(index=i+1,raw=k+1,root_without_roads=state,action=action.tolist(),station=q['s'],margin=gap,target=target,forces=force)
                    if old is not None:
                        j=len(trace);replay_exact &= j<len(old) and old[j]['root_without_roads']==json.loads(json.dumps(state)) and old[j]['action']==record['action']
                    trace.append(record)
                if minimum<.5:stop='MODEL_MARGIN';break
                if overspeed>5. or lateral>3. or peak>1.25 or (samples and clipped/samples>.10):stop='MODEL_DYNAMICS_GUARD';break
                if 'end' in events:stop='MODEL_WINDOW_END';break
            if old is not None:replay_exact &= len(trace)==len(old)
            passed=stop=='MODEL_WINDOW_END' and minimum>=.5 and overspeed<=5 and lateral<=3 and peak<=1.25 and (not samples or clipped/samples<=.10) and replay_exact
            item=dict(start=label,budget=budget,stop=stop,actions=actions,raw_ticks=len(trace),min_margin_m=minimum,max_lateral_path_error_m=lateral,max_tracking_overspeed_m_s=overspeed,peak_combined_force_ratio=peak,clipped_wheel_samples=clipped,wheel_samples=samples,baseline515_replay_exact=replay_exact if budget==80 else None,events=events,window_time_s=events['end']['time']-events['begin']['time'] if 'begin'in events and 'end'in events else None,pass_gate=passed)
            save(D/(label+'-'+str(int(budget))+'-model-private.json'),dict(summary=item,trace=trace));results.append(item)
    comparisons=[]
    for label in ('exact_reset','trigger_stress'):
        b=next(x for x in results if x['start']==label and x['budget']==80.);a=next(x for x in results if x['start']==label and x['budget']==100.)
        gain=b['window_time_s']-a['window_time_s'] if a['pass_gate'] and b['pass_gate'] else None
        comparisons.append(dict(start=label,window_time_gain_s=gain,information_gate=gain is not None and gain>=.08))
    eligible=all(x['pass_gate'] for x in results) and all(x['information_gate'] for x in comparisons)
    result=dict(status='MODEL_NATIVE_ELIGIBLE' if eligible else 'MODEL_NO_NATIVE',native_pair_eligible=eligible,arms=results,comparisons=comparisons,model_integrator_ticks=counter[0],model_wheel_force_evaluations=force_evals,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,native_actions=0,native_resets=0,native_worlds=0,research_remaining=25804,reserve=84000,reserve_used=0)
    guard();save(G/'retry/speed516_model_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
