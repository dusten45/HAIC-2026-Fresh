"""Bounded saved-only calibration and steering gates; never creates native world."""
import datetime,hashlib,json,math,resource,signal,subprocess,sys,time
from pathlib import Path
from dataclasses import asdict,replace
import numpy as np
from retry.plan512_control import tick,station
from retry.plan513_control import steering,steered,response_action,scalar_action
from retry.plan513_model import load_root,start_root,margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response513-private');OLD=Path('/workspace/haic-response512-private')

def run():
    start=time.perf_counter();cpu=time.process_time();child=resource.getrusage(resource.RUSAGE_CHILDREN);counter=[0]
    c=json.loads((G/'retry/plan513_contract.json').read_text())
    if (D/'MODEL_STARTED.json').exists():raise RuntimeError('NO_SCIENTIFIC_MODEL_RETRY')
    def usage():
        z=resource.getrusage(resource.RUSAGE_CHILDREN);return time.process_time()-cpu+z.ru_utime+z.ru_stime-child.ru_utime-child.ru_stime
    def guard(*a):
        if usage()>=120 or time.perf_counter()-start>=180:raise RuntimeError('MODEL_RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('MODEL_CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,120)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('MODEL_WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,180)
    def save(path,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode()
        if sum(p.stat().st_size for p in D.iterdir())+len(data)>64*1024**2 or len(list(D.iterdir()))>=3000:raise RuntimeError('STORAGE_CAP')
        with path.open('xb') as f:f.write(data)
        path.chmod(0o600 if D in path.parents else 0o644)
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in c['source_sha256'].items())
    for name,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h
    tests=subprocess.run([sys.executable,'-m','unittest','retry.test_plan512','retry.test_plan513','-v'],cwd=G,capture_output=True,text=True,timeout=30)
    save(D/'pure-tests.json',dict(returncode=tests.returncode,stdout=tests.stdout,stderr=tests.stderr))
    if tests.returncode:raise RuntimeError('PURE_GATE')
    snapshot=json.loads((OLD/'trigger-scalar-private.json').read_text());trigger=load_root(snapshot['root']);plan=snapshot['plan']
    raw={i:json.loads((OLD/('raw-%04d.json'%i)).read_text()) for i in range(51,51+4*28+1)}
    records=[json.loads((OLD/('action-scalar-%03d.json'%i)).read_text()) for i in range(1,30)]
    initial=start_root(trigger,raw[51],raw[52])
    mesh=json.loads(Path('/workspace/haic-response511-private/map-steady-private.json').read_text());roads=mesh['roads'];index=bounds(roads);edge=mesh['boundary'];ei=boundary_index(edge)
    save(D/'initial-reconstructed-private.json',dict(root=asdict(initial),limitations='No saved full reset planar state or solver warm-start. Layout rotated from trigger; reset State/position/contact observed, zero yaw/rates/momentum reconstructed. Requires factual replay gate; not exact snapshot.'))
    save(D/'MODEL_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/plan513_contract.json').read_bytes()).hexdigest()))
    calibration=[]
    for label,root,begin,end in [('reset_reconstructed',initial,1,24),('trigger_copied',trigger,25,28)]:
        errors=[];pmax=vmax=amax=ymax=mmax=0.;friction_errors=0
        for actionindex in range(begin,end+1):
            action=np.asarray(records[actionindex-1]['record']['action'],np.float32);root=steered(root,action)
            for k in range(4):
                guard();used=root.current_contacts;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);actual=raw[51+(actionindex-1)*4+k+1]
                pe=math.dist(root.center,actual['position']);ve=abs(math.hypot(*root.planar.linear.velocity)-actual['speed']);me=abs(margin(root,roads,index,edge,ei)-actual['margin'])
                pmax=max(pmax,pe);vmax=max(vmax,ve);mmax=max(mmax,me)
                # State before the NEXT actual action supplies actual yaw/angle.
                if k==3 and actionindex>=25:
                    nextroot=load_root(records[actionindex]['root']);ae=abs(math.remainder(root.planar.angle-nextroot.planar.angle,2*math.pi));ye=abs(root.planar.yaw-nextroot.planar.yaw);amax=max(amax,ae);ymax=max(ymax,ye)
                mu=lambda ids:max([root.floor,*[400*root.roads[i][1] for i in ids]])
                friction_errors+=sum(mu(a)!=mu(b) for a,b in zip(used,actual['used_contacts']))
                errors.append(dict(action=actionindex,raw=k+1,position_error=pe,speed_error=ve,margin_error=me))
        passed=pmax<=.10 and vmax<=.15 and amax<=.02 and ymax<=.05 and mmax<=.10 and friction_errors==0
        calibration.append(dict(root=label,actions=end-begin+1,ticks=4*(end-begin+1),max_position_error_m=pmax,max_speed_error_m_s=vmax,max_angle_error_rad=amax if begin==25 else None,max_yaw_error_rad_s=ymax if begin==25 else None,max_margin_error_m=mmax,friction_mismatches=friction_errors,pass_gate=passed))
        save(D/('calibration-'+label+'-private.json'),errors)
    calibration_pass=all(x['pass_gate'] for x in calibration);safety=[]
    if calibration_pass:
        # Factual future command arrays are calibration-only, never plan inputs.
        del raw,records
        for label,startroot,completed in [('reset_reconstructed',initial,0),('trigger_copied',trigger,24)]:
            for arm in ('scalar','response'):
                root=startroot;trace=[];minimum=float('inf');maximum_lateral=0.;stop='HOLD_CAP';elapsed=0.;crossing=None
                try:
                    for i in range(completed,200):
                        guard();steer=steering(root,plan);root=steered(root,[steer,0,0])
                        if i<24:action=np.array([steer,.32,0],np.float32)
                        else:action,details=(scalar_action(root,steer,plan) if arm=='scalar' else response_action(root,steer,plan,counter))
                        for k in range(4):
                            old=root;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),counter);elapsed+=.02
                            gap=margin(root,roads,index,edge,ei);minimum=min(minimum,gap)
                            lateral=abs((root.center[0]-plan['start'][0])*plan['axis'][1]-(root.center[1]-plan['start'][1])*plan['axis'][0]);maximum_lateral=max(maximum_lateral,lateral)
                            modelstate=asdict(root);modelstate.pop('roads')
                            trace.append(dict(action=i+1,raw=k+1,root_without_static_roads=modelstate,margin=gap))
                            if gap<.50:stop='MODEL_ROAD_MARGIN';break
                            if station(old.center,plan)<plan['gate']<=station(root.center,plan):
                                stop='MODEL_GATE';crossing=dict(elapsed_s=elapsed,speed_m_s=math.hypot(*root.planar.linear.velocity));break
                        if stop in ('MODEL_ROAD_MARGIN','MODEL_GATE'):break
                except ValueError as e:stop='MODEL_PLAN_STOP:'+str(e)
                safety.append(dict(start=label,arm=arm,stop=stop,model_raw_ticks=len(trace),min_margin_m=minimum,max_lateral_m=maximum_lateral,crossing=crossing,steering_safe_to_gate=stop=='MODEL_GATE' and minimum>=.50))
                save(D/('safety-'+label+'-'+arm+'-private.json'),trace)
    safety_pass=len(safety)==4 and all(x['steering_safe_to_gate'] for x in safety)
    result=dict(status='MODEL_PREFLIGHT_PASS' if calibration_pass and safety_pass else 'MODEL_PREFLIGHT_STOP',calibration=calibration,calibration_pass=calibration_pass,safety=safety,safety_pass=safety_pass,
        hypothetical_model_ticks=counter[0],CPU_s_including_test_child=usage(),wall_s=time.perf_counter()-start,native_worlds=0,native_resets=0,native_actions=0,research_remaining=25875,reserve=84000,reserve_used=0,
        limits='Rigid planar/joint approximation, no solver warm-start/broadphase history. Reset layout reconstructed; trigger copied. No universal safety claim. Four own predicted arm/start trajectories only; no protected data or future actual contact input to candidates.')
    save(G/'retry/plan513_preflight_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
