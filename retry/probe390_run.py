"""Frozen known-TRAIN instrumentation and one-action qualification; no fitting/sweep."""
import ast, datetime, fcntl, hashlib, json, random, sys, time, traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read, save, sha, projection
from retry.loss389_replay import sensor
G = Path(__file__).resolve().parent.parent

def verify(root, sources=False):
    d=root/'stage390';p=read(d/'plan.json')
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
    if sources:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
        for f,h in p['protected_hashes'].items():assert sha(f)==h,f
    return p

def charge(root, field, branch, count=1):
    d=root/'stage390'
    with (d/'budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);b=read(d/'budget.json')
        if field=='native':
            assert b['native']+count<=4774 and b[branch]+count<=(4000 if branch=='A' else 774)
            b[branch]+=count
        if field=='model_ticks':assert b[field]+count<=128
        b[field]=b.get(field,0)+count;save(d/'budget.json',b)

def control_code(path):
    tree=ast.parse(Path(path).read_text());loop=next(x for x in ast.walk(tree) if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='step')
    start=next(i for i,x in enumerate(loop.body) if isinstance(x,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='raw' for z in x.targets))
    end=next(i for i,x in enumerate(loop.body) if isinstance(x,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='action' for z in x.targets))
    module=ast.Module(body=loop.body[start:end+1],type_ignores=[])
    return compile(module,str(path),'exec'),hashlib.sha256(ast.dump(module,include_attributes=False).encode()).hexdigest()

def A(root):
    from retry.diagnose import make_env
    from retry.pace265_force import TireTrace
    d=root/'stage390';p=verify(root,True);assert not(d/'A-opening.json').exists();save(d/'A-opening.json',dict(epoch=time.time()))
    code,digest=control_code(G/'retry/pace265_run.py');assert digest==p['controller_AST_sha256'];out=[]
    for key in ['O0','N1']:
        f=d/('A-'+key);assert not f.exists();f.mkdir(mode=0o700);env=None;tire=TireTrace();rows=[];error=None;charged=ticks=reset=0;start,cpu=time.perf_counter(),time.process_time();complete=ended=truncated=False;info={};matched=0
        try:
            fixed=read(Path(p['A_plans'][key]));line=np.asarray(fixed['line']);prof=fixed['free_profile'];ds=np.asarray(prof['ds']);sarc=np.r_[0,np.cumsum(ds)]
            scope=dict(line=line,vprof=np.asarray(prof['speed']),ds=ds,curvature=np.asarray(prof['curvature']),sarc=sarc,L=sarc[-1],model=fixed['model'],index=0,laststeer=0.,pace=1.5)
            env=make_env();case=p['cases'][key];charge(root,'resets','A');obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;reset=round(raw.t*50);t0=raw.t
            assert hashlib.sha256(obs.tobytes()).hexdigest()==p['A_initial_pixels'][key]
            assert hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['cases'][key]['road_geometry_sha256'];scope['env']=env
            old=read(Path(p['A_references'][key])/'trajectory-private.json');oldresult=read(Path(p['A_references'][key])/'result.json');save(f/'fixed-geometry-private.json',dict(line=line.tolist(),road=np.asarray(raw.track)[:,2:4].tolist()))
            tire.enable()
            for step in range(1,2001):
                verify(root);pre=sensor(env);exec(code,dict(np=np),scope);action=scope['action'];i=scope['i'];u=scope['u'];model=scope['model'];feed=scope['feed'];feedback=scope['feedback'];acc=scope['acc'];speed=scope['speed']
                assert step<=len(old) and action.tolist()==old[step-1]['action'],('unchanged265 command',key,step)
                nearest=projection(line,np.asarray([pre['pos']]))
                control=dict(cursor_index=int(scope['index']),cursor_fraction=float(scope['index']+u),cursor_arc_m=float(scope['arc']),nearest_segment=int(nearest['index'][0]),nearest_fraction=float(nearest['index'][0]+(nearest['arc'][0]-sarc[nearest['index'][0]])/ds[nearest['index'][0]]),nearest_arc_m=float(nearest['arc'][0]),global_path_error_m=float(abs(nearest['lateral'][0])),cursor_path_error_m=scope['err'],target_speed_m_s=scope['desired'],feedforward_accel=feed,feedback_accel=feedback,command_accel=acc,positive_accel_clamped=feed+feedback>model['rear_traction_accel'],negative_accel_clamped=feed+feedback<-model['brake_accel'],gas_unclipped=model['effective_mass']*max(acc,0)*(speed+2.7)/80000,brake_unclipped=model['effective_mass']*max(-acc,0)/(4*1.6*15/(.02*.54)),action=action.tolist())
                charge(root,'native','A');charged+=1;tire.begin_action();before=raw.t;obs,_,ended,truncated,info=env.step(action);rt=round((raw.t-before)*50);ticks+=rt;assert len(tire.current)==rt*4
                post=sensor(env);assert bool(info['collision'])==old[step-1]['collision'] and post['visited']==old[step-1]['visited'] and env.damage.damage==old[step-1]['damage'],('unchanged265 outcomes',key,step);matched+=1
                rows.append(dict(step=step,pre=pre,post=post,control=control,collision=bool(info['collision']),tire=tire.summarize(),raw_ticks=rt,terminated=bool(ended),truncated=bool(truncated)));complete=raw.finish_time_s is not None
                if ended or truncated:break
            lap=round((raw.finish_time_s-t0)*1000) if complete else None
            assert charged==oldresult['native_actions'] and lap==oldresult['lap_ms'] and env.damage.damage==oldresult['damage'],('unchanged265 final',key)
        except BaseException as e:
            error=type(e).__name__+': '+str(e);save(f/'error-private.json',dict(error=error,traceback=traceback.format_exc()))
        finally:
            tire.disable()
            if env:env.close()
        save(f/'trace-private.json',rows)
        r=dict(case=key,native=charged,matched_rows=matched,raw_ticks=ticks,reset_ticks=reset,completed=complete,actual_DNF=bool(ended and not complete),censored=bool(error or not(ended or truncated)),lap_ms=lap if error is None else None,retire_reason=info.get('retire_reason'),technical_error=error,runner_CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,unconfirmed_charged_native=charged-len(rows));save(f/'result.json',r);out.append(r);print(json.dumps(r),flush=True)
        if error:break
    save(d/'A-outcome.json',dict(results=out,technical_error=next((r['technical_error'] for r in out if r['technical_error']),None)))

def B_episode(root,label,target=None,arm='original'):
    from retry.diagnose import make_env
    from retry.frozen_composite_runtime import prepare,validate_response
    from retry.source_vehicle_transition import capture
    from retry.pedal331_run import rng
    from retry.pace265_force import TireTrace
    d=root/'stage390';p=verify(root,True);f=d/label;assert not f.exists();f.mkdir(mode=0o700)
    if arm!='original':assert read(d/'B-model-gate.json')['passed']
    maxstep=max(x['step'] for x in p['B_states']) if target is None else target
    baseline=[json.loads(s) for s in (root/'stage389/replay/N1/trace-private.jsonl').read_text().splitlines()]
    env=worker=None;steps=ticks=reset=0;actorcpu=0.;error=None;rows=[];captures={};reaping=None;start,cpu=time.perf_counter(),time.process_time();changed=None
    random.seed(375);np.random.seed(375);tire=TireTrace()
    try:
        cfg=p['config'];worker=prepare(cfg,f/'cpu',p['sandbox_path']);charge(root,'resets','B');env=make_env();case=p['cases']['N1'];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;reset=round(raw.t*50)
        assert capture(env)==read(root/'stage389/replay/N1/initial-scene-private.json')
        charge(root,'actor_resets','B');res,_=worker.call('reset',obs);validate_response(res,cfg,obs,'reset');tire.enable()
        for step in range(1,maxstep+1):
            verify(root);pre=sensor(env);assert pre==baseline[step-1]['pre'],('actualprefixstate',label,step)
            charge(root,'actor_act','B');res,_=worker.call('act',obs);a=validate_response(res,cfg,obs,'act');assert a.tolist()==baseline[step-1]['action'] and res['features']==baseline[step-1]['features']
            selected=step in [x['step'] for x in p['B_states']]
            if selected:
                cap=dict(snapshot=capture(env),RNG=rng(env),actor_state=res['state'],action=a.tolist(),features=res['features']);captures[str(step)]=cap
                if arm!='original':
                    ref=read(d/'B-capture/captures-private.json')[str(step)];ref={k:v for k,v in ref.items() if k not in ['actual_post','actual_collision']};assert cap==ref,('fullphysical_RNG_actor_boundary',label,step)
            command=a.copy()
            if step==target:
                if arm=='no_brake':command[2]=0
                elif arm=='full_gas_no_brake':command[1:]=[1,0]
                else:assert arm=='original'
            charge(root,'actor_commit','B');ack,_=worker.call('commit',command);actorcpu=ack['actor_cumulative_CPU_s'];assert ack['memory']==ack['nominal_memory']==res['state']['previous_steer']
            charge(root,'native','B');steps+=1;tire.begin_action();before=raw.t;obs,_,ended,truncated,info=env.step(command);rt=round((raw.t-before)*50);ticks+=rt;post=sensor(env)
            row=dict(step=step,pre=pre,post=post,command=command.tolist(),original=a.tolist(),collision=bool(info['collision']),damage=float(env.damage.damage),raw_ticks=rt,actor_memory=ack['memory'],tire=tire.summarize());rows.append(row);assert len(tire.current)==rt*4
            if target is None or step<target:assert post==baseline[step-1]['post'] and row['collision']==baseline[step-1]['collision'] and row['damage']==baseline[step-1]['damage']
            if selected and arm=='original':captures[str(step)]['actual_post']=post;captures[str(step)]['actual_collision']=row['collision']
            if step==target:changed=row
            assert not ended and not truncated,('unexpectedterminal',label,step)
    except BaseException as e:error=type(e).__name__+': '+str(e);save(f/'error-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        tire.disable()
        if worker:reaping=worker.close()
        if env:env.close()
    save(f/'trace-private.json',rows);save(f/'captures-private.json',captures)
    r=dict(label=label,target=target,arm=arm,native=steps,raw_ticks=ticks,reset_ticks=reset,actor_CPU_s=actorcpu,runner_CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,technical_error=error,unconfirmed_charged_native=steps-len(rows),reaping=reaping,matched_prefix_rows=len(rows) if target is None else max(0,len(rows)-1));save(f/'result.json',r);print(json.dumps(r),flush=True);return r

def B_model(root):
    from retry.source_vehicle_transition import SourceVehicleTransition
    d=root/'stage390';p=verify(root,True);assert not(d/'B-model-opening.json').exists();save(d/'B-model-opening.json',dict(epoch=time.time()));assert read(d/'B-capture/result.json')['technical_error'] is None
    caps=read(d/'B-capture/captures-private.json');records=[];predictions=[];start,cpu=time.perf_counter(),time.process_time();error=None
    def trial(s,a):
        assert time.process_time()-cpu<1800;verify(root);m=SourceVehicleTransition(s)
        try:
            initial=dict(bodies=m.initial_bodies_exact,tiles=m.initial_tiles_exact,progress=m.initial_progress_exact)
            charge(root,'model_ticks','B',4);q=m.step(a);assert m.native_ticks==4;return q,initial
        finally:m.close()
    try:
        for sel in p['B_states']:
            c=caps[str(sel['step'])];q,initial=trial(c['snapshot'],c['action']);post=c['actual_post'];err=dict(speed_m_s=abs(q['speed_m_s']-post['speed']),yaw_rate_rad_s=abs(q['angular_velocity']-post['yaw']),position_m=float(np.linalg.norm(np.array(q['position'])-post['pos'])))
            discrete=dict(collision=q['collision']==c['actual_collision'],damage=q['damage']==c['snapshot']['damage'],road_contacts=q['wheel_road_contacts']==sum(n>0 for n in post['road_contacts']))
            passed=all(initial.values()) and all(err[k]<=v for k,v in p['B_model_limits'].items()) and all(discrete.values())
            records.append(dict(step=sel['step'],phase=sel['phase'],errors=err,initialization=initial,discrete=discrete,passed=passed,predicted=q))
        passed=bool(records) and len(records)==len(p['B_states']) and all(r['passed'] for r in records)
        if passed:
            for sel in p['B_states']:
                c=caps[str(sel['step'])]
                for arm in ['no_brake','full_gas_no_brake']:
                    a=np.array(c['action'],np.float32);a[2]=0
                    if arm=='full_gas_no_brake':a[1]=1
                    q,initial=trial(c['snapshot'],a);predictions.append(dict(step=sel['step'],arm=arm,action=a.tolist(),predicted=q,initialization=initial))
    except BaseException as e:
        passed=False;error=type(e).__name__+': '+str(e);save(d/'B-model-error-private.json',dict(error=error,traceback=traceback.format_exc()))
    save(d/'B-model-predictions-private.json',predictions);save(d/'B-model-gate.json',dict(passed=passed,records=records,technical_error=error,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,source_physics_ticks=read(d/'budget.json')['model_ticks'],scope='One-action same-actual-state qualification only; failure withholds this model MPC, not joint-optimization family'));print(json.dumps(dict(B_model_gate=passed,records=records,error=error)),flush=True)

def B_pulses(root):
    p=verify(root,True);d=root/'stage390';assert read(d/'B-model-gate.json')['passed']
    for s in p['B_states']:
        for arm in ['no_brake','full_gas_no_brake']:
            r=B_episode(root,'B-'+str(s['step'])+'-'+arm,s['step'],arm)
            if r['technical_error']:return

if __name__=='__main__':
    root=Path(sys.argv[1]).resolve();mode=sys.argv[2]
    if mode=='A':A(root)
    elif mode=='B0':B_episode(root,'B-capture')
    elif mode=='model':B_model(root)
    elif mode=='pulses':B_pulses(root)
    else:raise ValueError(mode)
