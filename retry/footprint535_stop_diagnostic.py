"""Bounded saved-root diagnostic after the sole nativepair; no newworld/action."""
import datetime,hashlib,json,math,time,signal
from collections import Counter
from pathlib import Path
import numpy as np
from retry.footprint535_control import choose,certifier,geometry_context
from retry.response528_control import choose as old_choose
from retry.plan513_model import load_root
from retry.frozen534_projection import initial_progress
from retry.lap518_control import nominal
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response535-recovery-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/footprint535_stop_contract.json').read_text());assert not (D/'STOP_DIAGNOSTIC_STARTED.json').exists()
    for file,h in c['source_sha256'].items():assert hashlib.sha256((G/file).read_bytes()).hexdigest()==h
    for file,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==h
    (D/'STOP_DIAGNOSTIC_STARTED.json').write_text(json.dumps(dict(contract_sha256=hashlib.sha256((G/'retry/footprint535_stop_contract.json').read_bytes()).hexdigest())))
    counter=[0];cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0)
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    from core.vendor.car_racing import CarRacing
    def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=poison
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());cold=json.loads(Path('/workspace/haic-response535-private/cold-candidate-model-private.json').read_text());geo=geometry_context(static,13000);rows=[];differences=[]
    def load(x):return load_root(dict(x,roads=static['root']['roads']))
    def guard():
        if counter[0]>12000 or cost['force_evaluations']>60000 or time.process_time()-cpu>180 or time.perf_counter()-wall>240:raise RuntimeError('DIAGNOSTIC_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    for index in (32,33):
        actual=json.loads((D/f'action-candidate-{index-1:03d}.json').read_text())['after_root_without_roads'];model=next(z['root_without_roads'] for z in cold['trace'] if z['index']==index-1 and z['raw']==4);a=load(actual);b=load(model);differences.append(dict(before_action=index,position_m=math.dist(a.center,b.center),velocity_vector_m_s=math.dist(a.planar.linear.velocity,b.planar.linear.velocity),angle_rad=abs(math.remainder(a.planar.angle-b.planar.angle,2*math.pi)),yaw_rad_s=abs(a.planar.yaw-b.planar.yaw),wheel_omega_max=float(max(abs(x.omega-y.omega) for x,y in zip(a.planar.linear.wheels,b.planar.linear.wheels))),lever_max_m=float(max(math.dist(x,y) for x,y in zip(a.planar.levers,b.planar.levers))),relative_joint_max_rad=float(max(abs(x-y) for x,y in zip(a.planar.joints,b.planar.joints))),wheel_relative_rates_max_rad_s=float(max(abs(x-y) for x,y in zip(a.planar.rates,b.planar.rates)))))
        for kind,root in [('actual',a),('model',b)]:
            guard();s=initial_progress(root,paths['candidate'],index-1);history=(0,(index-1-24)*16);action,detail=choose(root,paths['candidate'],paths['backup'],s,counter,cost,12000,history=history,geometry=geo);reports=detail.get('trials',detail.get('reports',[]));grid=[];force_only=None
            if kind=='actual' and index==33:
                old_action,old_detail=old_choose(root,paths['candidate'],paths['backup'],s,counter,cost,12000,history=history);force_only=dict(mode=old_detail['mode'],available=old_action is not None);cert=certifier(root,paths['candidate'],paths['backup'],s,counter,cost,geo,12000,history);lock=np.float32(.9)
                if float(lock)<.9:lock=np.nextafter(lock,np.float32(1.))
                values=sorted(set([float(np.float32(-1+i/4)) for i in range(9)]+[-float(lock),-float(np.nextafter(lock,np.float32(0.)))]));steer=nominal(root,paths['candidate'],s)[0]
                for u in values:
                    guard();report=cert(np.array([steer,max(0.,u),max(0.,-u)],np.float32));grid.append(dict(u=u,report=report))
            row=dict(root=kind,before_action=index,mode=detail['mode'],safe_command=action is not None,force_only_controller=force_only,certificate_failure_reasons=dict(Counter(x['reason'] for x in reports if not x['ok'])),HIGH_report=detail.get('reports',[None])[0],FINAL_report=next((x for x in detail.get('reports',[]) if x['mode']=='FINAL'),None),full_signed_grid_count=len(grid),full_signed_grid_safe_count=sum(x['report']['ok'] for x in grid),full_signed_grid_first_hold_safe_count=sum(x['report']['first_hold_pass'] for x in grid),full_signed_grid_failure_reasons=dict(Counter(x['report']['reason'] for x in grid if not x['report']['ok'])));rows.append(row)
            with (D/f'stop-{kind}-{index}-private.json').open('x') as f:json.dump(dict(summary=row,detail=detail,grid=grid,action=None if action is None else action.tolist()),f,indent=2)
    guard();out=dict(rows=rows,actual_vs_model_differences=differences,model_integrator_ticks=counter[0],source_force_evaluations_in_integrator=4*counter[0],explicit_force_evaluations=cost['force_evaluations'],cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,native_resets=0,scope='Savedactual/modelcurrentroots,unchanged535policy/futurebackup. Noactualfuturetraceinput,nonewcontrol/nativetry. Predictedfailureisnotobservedfuturecollisionorproofallpedalpoliciesimpossible.')
    with (G/'retry/footprint535_stop_diagnostic.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
