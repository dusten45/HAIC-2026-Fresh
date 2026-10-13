"""Privileged wheel-force tracing of unchanged Car.step on existing240 snapshots.

Reads Python locals before/after friction clipping; no source/body mutation.
Same-state3-action brake/gas-removal shadows, never runtime policy inputs.
"""
import argparse,json,time,hashlib,inspect,sys
from pathlib import Path
import numpy as np


def forecast(snapshot,commands,instrument=False):
    from core.vendor.car_dynamics import Car
    from retry.source_vehicle_transition import SourceVehicleTransition
    from retry.receding_horizon_oracle import contiguous_visited_tiles
    start=time.perf_counter();model=SourceVehicleTransition(snapshot);records=[];pending={};omega_before={};rows=[]
    lines,first=inspect.getsourcelines(Car.step);pre=first+next(i for i,l in enumerate(lines) if 'if abs(force) > 2.0 * friction_limit:' in l);post=first+next(i for i,l in enumerate(lines) if 'w.omega -= dt * f_force' in l);before=first+next(i for i,l in enumerate(lines) if 'w.omega += (' in l)
    def trace(frame,event,arg):
        if frame.f_code is not Car.step.__code__:return None
        if event=='line' and frame.f_lineno in [before,pre,post]:
            local=frame.f_locals;w=local['w'];idx=next(i for i,x in enumerate(local['self'].wheels) if x==w)
            if frame.f_lineno==before:omega_before[idx]=float(w.omega)
            elif frame.f_lineno==pre:
                pending[idx]=dict(physics_tick=len(records)//4+1,wheel=idx,omega_before=omega_before[idx],omega_after_engine_brake=float(w.omega),wheel_surface_speed=float(local['vr']),wheel_forward_speed=float(local['vf']),wheel_lateral_speed=float(local['vs']),slip_speed=float(local['vr']-local['vf']),raw_long_N=float(local['f_force']),raw_lat_N=float(local['p_force']),friction_limit_N=float(local['friction_limit']),raw_force_N=float(local['force']))
            else:
                r=pending.pop(idx);f=float(local['f_force']);p=float(local['p_force']);body_forward=local['self'].hull.GetWorldVector((0,1));body_side=local['self'].hull.GetWorldVector((1,0));global_force=np.asarray(local['forw'])*f+np.asarray(local['side'])*p;r.update(applied_long_N=f,applied_lat_N=p,clipped=r['raw_force_N']>r['friction_limit_N'],body_forward_N=float(global_force@np.asarray(body_forward)),body_lateral_N=float(global_force@np.asarray(body_side)));records.append(r)
        return trace
    old=sys.gettrace()
    try:
        if instrument:sys.settrace(trace)
        for action in commands:
            row=model.step(np.asarray(action,np.float32));row['contiguous']=contiguous_visited_tiles({int(t.idx) for t in model.roads if t.road_visited},snapshot['road_count']);rows.append(row)
            if row['terminal']:break
    finally:
        sys.settrace(old);model.close()
    if instrument:assert len(records)==model.native_ticks*4
    return dict(rows=rows,forces=records,physics_ticks=model.native_ticks,wall_s=time.perf_counter()-start,initialization=dict(tiles=model.initial_tiles_exact,progress=model.initial_progress_exact,bodies=model.initial_bodies_exact))


def run(path):
    p=json.loads(path.read_text());D=path.parent
    def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
    def read(q):return json.loads(q.read_text())
    def save(q,x):
        t=q.with_name(q.name+'.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.chmod(0o600);t.replace(q)
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(q)==h
    assert not (D/'opening.json').exists(),'One-use model diagnosis; completed queries never repeated'
    save(D/'opening.json',dict(start_epoch=time.time()));start=time.perf_counter();cpu=time.process_time();modelticks=0;queries=0;results=[];verification=[];error=None
    try:
        for road in p['road_order']:
            m=read(Path(p['materializations'][road]));z=np.load(Path(p['materializations'][road]).parent/'cache-private.npz');commands=z['commands']
            for job in [j for j in p['jobs'] if j['road']==road]:
                a=job['action'];snapshot=m['snapshots'][str(a)];seq=commands[a-1:a+2];variants={'baseline':seq.copy(),'no_brake':seq.copy(),'no_gas':seq.copy()};variants['no_brake'][:,2]=0;variants['no_gas'][:,1]=0;trials={}
                for name,controls in variants.items():
                    assert np.array_equal(controls[:,0],seq[:,0]);q=forecast(snapshot,controls,True);queries+=1;modelticks+=q['physics_ticks'];save(D/(road+'_'+str(a)+'_'+name+'-private.json'),q);forces=q['forces']
                    def group(indices):
                        f=[x for x in forces if x['wheel'] in indices];ticks=sorted({x['physics_tick'] for x in f});return dict(mean_applied_body_forward_N=float(np.mean([sum(x['body_forward_N'] for x in f if x['physics_tick']==t) for t in ticks])),mean_applied_body_lateral_N=float(np.mean([sum(x['body_lateral_N'] for x in f if x['physics_tick']==t) for t in ticks])),clipped_fraction=float(np.mean([x['clipped'] for x in f])),mean_slip_m_s=float(np.mean([x['slip_speed'] for x in f])),mean_raw_long_N=float(np.mean([x['raw_long_N'] for x in f])),mean_applied_long_N=float(np.mean([x['applied_long_N'] for x in f])),mean_raw_lat_abs_N=float(np.mean([abs(x['raw_lat_N']) for x in f])),mean_applied_lat_abs_N=float(np.mean([abs(x['applied_lat_N']) for x in f])),mean_omega_rad_s=float(np.mean([x['omega_after_engine_brake'] for x in f])))
                    tickgroups=[[x for x in forces if x['physics_tick']==t] for t in sorted({x['physics_tick'] for x in forces})];cancellation=np.mean([sum(abs(x['body_forward_N']) for x in f)-abs(sum(x['body_forward_N'] for x in f)) for f in tickgroups]);trials[name]=dict(front=group([0,1]),rear=group([2,3]),total=group([0,1,2,3]),mean_opposing_longitudinal_cancellation_N=float(cancellation),end_speed_m_s=q['rows'][-1]['speed_m_s'],end_damage=q['rows'][-1]['damage'],contact=any(r['collision'] for r in q['rows']),terminal=q['rows'][-1]['terminal'],new_contiguous=q['rows'][-1]['contiguous']-next((i for i in range(snapshot['road_count']) if not snapshot['roads'][i]['visited']),snapshot['road_count']))
                for name in ['no_brake','no_gas']:trials[name]['end_speed_delta_m_s']=trials[name]['end_speed_m_s']-trials['baseline']['end_speed_m_s']
                results.append(dict(road=road,action=a,group=job['group'],trials=trials))
                if job.get('verify'):
                    frozen=commands[a-1:a+11];plain=forecast(snapshot,frozen,False);traced=forecast(snapshot,frozen,True);queries+=2;modelticks+=plain['physics_ticks']+traced['physics_ticks'];assert plain['rows']==traced['rows'],'Tracing changedsource endpoint'
                    actual=m['actual'][a-1:a+11];errors={k:0. for k in p['match_limits']};mismatch=0
                    for x,y in zip(actual,plain['rows']):
                        mismatch+=sum(x[k]!=y[k] for k in ['unique_tiles','collision','wheel_road_contacts','off_track_counter','terminal'])+int(x['contiguous']!=y['contiguous'])
                        for k,v in [('position_error_m',np.linalg.norm(np.asarray(x['position'])-y['position'])),('speed_error_m_s',abs(x['speed_m_s']-y['speed_m_s'])),('angle_error_rad',abs(x['angle']-y['angle'])),('damage_error',abs(x['damage']-y['damage']))]:errors[k]=max(errors[k],float(v))
                    valid=len(actual)==len(plain['rows'])==12 and mismatch==0 and all(errors[k]<=v for k,v in p['match_limits'].items());assert valid,'Existingbaseline replay limits failed';verification.append(dict(road=road,action=a,trace_bit_exact=True,actual12step_match=True,errors=errors,discrete_mismatches=mismatch));save(D/(road+'_'+str(a)+'-verification-private.json'),dict(receipt=verification[-1],plain=plain,traced=traced))
                save(D/'progress-private.json',dict(results=results,verification=verification,model_queries=queries,model_ticks=modelticks))
    except Exception as e:error=type(e).__name__+': '+str(e)
    save(D/'outcome-private.json',dict(stage=255,results=results,verification=verification,model_queries=queries,model_ticks=modelticks,native_actions=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,technical_error=error))

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
