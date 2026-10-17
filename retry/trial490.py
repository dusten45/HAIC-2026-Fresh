"""One490 frozen-source executor input build and zero-integration diagnostics."""
import time
START=time.perf_counter()
import ast,datetime,hashlib,io,json,math,os,resource,signal,sys,traceback
from pathlib import Path
from types import SimpleNamespace
for _var in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[_var]='1'
import numpy as np
from retry.quota489 import Quota
from retry.executor490_input import array_sha,load,bind

G=Path(__file__).resolve().parents[1];RAW=Path('/tmp/haic-retry-stage490-private');MIB=1024**2
DEADLINE='2026-10-20T10:01:55Z'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def function(path,name,scope):
    t=ast.parse(Path(path).read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[f],type_ignores=[]),str(path)+'#frozen490','exec'),scope)
    return scope[name],hashlib.sha256(ast.dump(f,include_attributes=False).encode()).hexdigest()
def archive(**arrays):
    stream=io.BytesIO();np.savez(stream,**arrays);return stream.getvalue()
class Stop(RuntimeError):pass

def run(root):
    root=Path(root);assert not RAW.exists(),'490_NO_RETRY';RAW.mkdir(mode=0o700)
    q=Quota(RAW);q.MAX_FILES=20;q.MAX_BYTES=8*MIB-256*1024;q.FILE_BYTES=MIB;q.TEMP_BYTES=MIB
    resource.setrlimit(resource.RLIMIT_AS,(256*MIB,256*MIB));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
    reg=read(G/'retry/executor490_registration.json');caps=reg['work_caps'];counts={k:0 for k in caps}
    summary=None;error=None;status='PREPARING'
    def usage():return dict(CPU_s=time.process_time(),wall_s=time.perf_counter()-START,RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    def remain():return (datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00'))-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    def check(closing=False):
        z=usage()
        if z['CPU_s']>=(29 if closing else 26) or z['wall_s']>=(44 if closing else 39) or z['RSS_bytes']>256*MIB or remain()<=0:raise Stop('490_TIME_MEMORY_DEADLINE')
        q.diskpreflight()
    def charge(k,n=1):
        check();assert type(n) is int and n>=0
        if counts[k]+n>caps[k]:raise Stop('490_WORK_CAP:'+k)
        counts[k]+=n
        q.write_json('stop.json',dict(state='PRECHARGED',counts=counts.copy(),resource=usage()),control=True)
    def alarm(*args):raise Stop('490_INTERRUPT')
    for sig in (signal.SIGPROF,signal.SIGALRM,signal.SIGTERM):signal.signal(sig,alarm)
    signal.setitimer(signal.ITIMER_PROF,max(.001,28-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,min(42-(time.perf_counter()-START),remain())))
    try:
        check();q.diskpreflight(9*MIB)
        for rel,h in reg['source_sha256'].items():assert sha(G/rel)==h
        pinpath=root/'stage490-input-pins-private.json';assert sha(pinpath)==reg['private_input_manifest_sha256']
        for path,h in read(pinpath).items():assert sha(path)==h
        budget=read(root/'project-effective-budget-v485.json');assert budget['research_remaining']==26175 and budget['final_reserved_actions']==84000 and budget['final_reserve_used']==0
        q.write_json('plan-private.json',dict(registration_sha256=sha(G/'retry/executor490_registration.json'),counts=counts,resource=usage(),deadline_utc=DEADLINE),exclusive=True)
        scope=dict(np=np,math=math)
        curvature,ksha=function(G/'retry/racing258_plan.py','curvature',scope)
        profile,psha=function(G/'retry/racing258_plan.py','profile',scope)
        multiplier,msha=function(G/'retry/pace268_profile.py','multipliers',dict(np=np))
        project_four,p4sha=function(G/'retry/analyze466.py','project_four',dict(np=np,math=math))
        proxy,xsha=function(G/'retry/analyze466.py','segment_proxy',dict(np=np,math=math))
        from retry.signed417_executor import canonical_projection,CoherentExecutor,ExecutorDomainError
        from retry.scalar392_audit import pedals
        assert not any(x.startswith(('Box2D','env_wrapper','core.vendor.car_racing')) for x in sys.modules)
        old=Path('/tmp/haic-retry-stage489-private');lineowner=old/'candidate-private.npz';certowner=old/'certificate-private.json'
        modelowner=Path('/tmp/haic-retry-stage485-private/native/D485-A/unsupported-geometry-private.json')
        with np.load(lineowner,allow_pickle=False) as z:line=z['line'];offset=z['offset']
        line.setflags(write=False);linehash=array_sha(line);assert linehash==read(certowner)['geometry']['path_sha256']
        model=read(modelowner)['model'];coeff=read(root/'stage268/selected-private.json')['coefficients'];n=len(line);assert n==321
        mass=model['mass'];assert all(math.isfinite(x) and x>0 for x in model.values())
        assert model==dict(mass=mass,effective_mass=mass+4*1.6/.54**2,rear_traction_accel=.8*800/(mass+2*1.6/.54**2),brake_accel=.3*(4*1.6*15/(.02*.54))/(mass+4*1.6/.54**2),lateral_accel=.4*1600/mass)
        charge('input_builds');charge('profile_calls')
        prof=profile(line,model);assert array_sha(line)==linehash
        charge('pace_calls');pace=multiplier(coeff,prof['curvature'],prof['ds'],model)
        scaled=prof['speed']*pace
        charge('p4_calls');charge('p4_passes',4);nodes=project_four(scaled,prof['ds'],model)
        assert array_sha(line)==linehash and nodes[0]==0 and np.isfinite(nodes).all() and np.all(nodes[1:]>0) and np.all(nodes<=scaled)
        assert np.isfinite(prof['speed']).all() and prof['speed'][0]==0 and np.all(prof['speed'][1:]>0)
        oldcurvature=np.asarray(read(certowner)['curvature'],dtype=np.float64)
        assert oldcurvature.tobytes()==prof['curvature'].tobytes()
        assert prof['ds'].tobytes()==np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1).tobytes()
        # Geometry/offset certificate is inherited only through authenticated
        # unchanged owner+line bytes; no path conversion or new source solve.
        assert np.all(abs(offset)<=40/6-1.4-.35) and read(certowner)['geometry']['tube_certificate']
        q.write_bytes('arrays-private.npz',archive(speed=prof['speed'],ds=prof['ds'],pace=pace,projected_nodes=nodes),exclusive=True)
        manifest=dict(stage=490,line_owner=str(lineowner),curvature_owner=str(certowner),model_owner=str(modelowner),arrays_owner=str(RAW/'arrays-private.npz'),owners={str(p):sha(p) for p in (lineowner,certowner,modelowner,RAW/'arrays-private.npz')},line_sha256=linehash,nodes_sha256=array_sha(nodes),curvature_sha256=array_sha(prof['curvature']),input_arrays_shapes=dict(line=[n,2],ds=[n],curvature=[n],speed=[n+1],pace=[n+1],projected_nodes=[n+1]),frozen_AST_sha256=dict(curvature=ksha,profile=psha,multipliers=msha,project_four=p4sha,segment_proxy=xsha),no_duplicate_line_raw=True,whole_map_privileged=True)
        q.write_json('input-manifest-private.json',manifest,exclusive=True)
        fixed,loadedpace,loadednodes=load(RAW/'input-manifest-private.json')
        # Exact paired417 policy AST, without its world-bearing module imports.
        policy,policysha=function(G/'retry/paired417_common.py','policy',dict(np=np,CoherentExecutor=CoherentExecutor))
        charge('executor_instances');consumer=policy(fixed,loadedpace);bind(consumer,loadednodes)
        assert consumer.line.tobytes()==line.tobytes() and consumer.nodes.tobytes()==nodes.tobytes()
        assert consumer.ds.tobytes()==prof['ds'].tobytes()
        # Frozen original cursor prefix only; no steering/action/world code.
        tree=ast.parse((G/'retry/pace269_run.py').read_text());loop=next(x for x in ast.walk(tree) if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='step')
        start=next(i for i,x in enumerate(loop.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='raw' for t in x.targets))
        end=next(i for i,x in enumerate(loop.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='arc' for t in x.targets))
        cursor_ast=ast.Module(body=loop.body[start:end+1],type_ignores=[]);cursor_code=compile(cursor_ast,'pace269_run.py#original-cursor490','exec')
        ds=prof['ds'];sarc=np.r_[0,np.cumsum(ds)];L=float(sarc[-1]);edges=np.roll(line,-1,axis=0)-line
        def canonical(path,pos,vel,phase):
            charge('canonical_queries');return canonical_projection(path,pos,vel,phase)
        def cursor(pos,vel,index):
            charge('original_cursor_queries')
            env=SimpleNamespace(unwrapped=SimpleNamespace(car=SimpleNamespace(hull=SimpleNamespace(position=pos,linearVelocity=vel))))
            local=dict(np=np,env=env,line=line,ds=ds,sarc=sarc,L=L,index=index)
            exec(cursor_code,dict(np=np),local);return int(local['i']),float(local['arc']),float(local['err']),int(local['index'])
        records=[];projection_errors=0;on_mismatch=off_mismatch=stale_mismatch=0;near_gap_min=math.inf;max_arc_gap=0.;max_stale_gap=0.
        for i in range(n):
            tangent=edges[i]/ds[i];normal=np.array([tangent[1],-tangent[0]])
            for kind,fraction,shift in [('vertex',0.,0.),('mid',.5,0.)]+[('off',.5,x) for x in (-3.,-1.,-.25,.25,1.,3.)]:
                pos=line[i]+fraction*edges[i]+shift*normal
                try:
                    z=canonical(line,pos,tangent,'LAUNCH' if i==0 and fraction==0 else 'FIRST_LAP')
                    j,arc,err,_=cursor(pos,tangent,i)
                    gap=abs((arc-z['arc']+L/2)%L-L/2);mismatch=(j!=z['index'] or gap>1e-8)
                    if kind=='off':off_mismatch+=mismatch
                    else:on_mismatch+=mismatch
                    max_arc_gap=max(max_arc_gap,gap)
                    # Distance gap to nonlocal (excluding adjacent) competitors.
                    charge('competitor_distance_batches')
                    v=edges;u=np.clip(np.sum((pos-line)*v,axis=1)/np.sum(v*v,axis=1),0,1);d=np.linalg.norm(pos-(line+u[:,None]*v),axis=1)
                    exclude={(z['index']-1)%n,z['index'],(z['index']+1)%n};competitor=min(float(d[h]) for h in range(n) if h not in exclude)
                    near_gap_min=min(near_gap_min,competitor-z['path_error_m'])
                    records.append([i,0 if kind=='vertex' else 1 if kind=='mid' else 2,shift,z['index'],j,gap,z['path_error_m'],competitor-z['path_error_m']])
                except ExecutorDomainError:projection_errors+=1;records.append([i,3,shift,-1,-1,0.,0.,0.])
            pos=line[i]+.5*edges[i];z=canonical(line,pos,tangent,'FIRST_LAP');j,arc,err,_=cursor(pos,tangent,max(0,i-18))
            gap=abs((arc-z['arc']+L/2)%L-L/2);stale_mismatch+=(j!=z['index'] or gap>1e-8);max_stale_gap=max(max_stale_gap,gap)
        # Unmodified seam-side policy, plus generic exact-tie/discontinuity case.
        q0=canonical(line,line[0],edges[0]/ds[0],'LAUNCH');qN=canonical(line,line[0],edges[-1]/ds[-1],'FIRST_LAP')
        assert q0['arc']==0 and qN['arc']==L and q0['index']==0 and qN['index']==n-1
        toy=np.array([[-4.,-1.],[4.,-1.],[4.,1.],[-4.,1.]])
        ambiguous=False
        try:canonical(toy,np.array([0.,0.]),np.array([1.,0.]),'FIRST_LAP')
        except ExecutorDomainError:ambiguous=True
        low=canonical(toy,np.array([0.,-1e-6]),np.array([1.,0.]),'FIRST_LAP');high=canonical(toy,np.array([0.,1e-6]),np.array([1.,0.]),'FIRST_LAP')
        assert ambiguous and low['index']!=high['index']
        charge('segment_proxy_checks',n)
        curve=np.r_[prof['curvature'],prof['curvature'][0]]
        rows=[proxy(nodes[i]**2,nodes[i+1]**2,curve[i],curve[i+1],ds[i],model) for i in range(n)]
        forward=max(x['discrete_forward_q_residual'] for x in rows);backward=max(x['discrete_backward_q_residual'] for x in rows)
        scalar=[]
        for i in range(n):
            r=math.sqrt((nodes[i]**2+nodes[i+1]**2)/2);f=(nodes[i+1]**2-nodes[i]**2)/(2*ds[i])
            for v,sigma in ((r,r),(0.,0.),(1.2*r,1.2*r)):
                charge('scalar_pedal_queries');raw=f*sigma/r+1.5*(r-v);z=pedals(raw,v,model)
                assert all(math.isfinite(z[k]) for k in z) and 0<=z['gas']<=1 and 0<=z['brake']<=1 and not(z['gas']>0 and z['brake']>0)
                if v==0:assert raw>0 and z['brake']==0
                scalar.append([i,v,sigma,raw,z['command_accel'],z['gas'],z['brake']])
        # Phase helper checks use the one consumer instance and pure inputs.
        synthetic_finish=dict(finish_time_s=None,candidate_crossing_time_s=None)
        charge('pure_executor_act_queries');charge('canonical_queries');a0,d0=consumer.act(dict(time=0.,speed=0.,pos=line[0],vel=[0.,0.]),np.array([0.,.25,0.],np.float32),synthetic_finish,0.)
        charge('pure_executor_act_queries');charge('canonical_queries');a1,d1=consumer.act(dict(time=.08,speed=0.,pos=line[0]+.05*edges[0],vel=[0.,0.]),np.array([0.,.25,0.],np.float32),synthetic_finish,.05*ds[0])
        assert d0['phase']=='LAUNCH' and d1['phase']=='FIRST_LAP' and d1['r']>0 and a1[2]==0
        assert array_sha(line)==linehash and consumer.line.tobytes()==line.tobytes() and consumer.nodes.tobytes()==nodes.tobytes()
        q.write_bytes('diagnostics-private.npz',archive(projection=np.asarray(records),scalar=np.asarray(scalar)),exclusive=True)
        q.write_json('segments-private.json',dict(segments=rows),exclusive=True)
        forward_bad=sum(x['discrete_forward_q_residual']>1e-8 for x in rows);back_bad=sum(x['discrete_backward_q_residual']>1e-8 for x in rows)
        schema=True;discrete_ok=forward_bad==back_bad==0
        summary=dict(line_bytes_unchanged=True,line_sha256=linehash,input_schema_passed=schema,complete_executor_input_candidate=True,final_P4_bound_without_double_pace=True,geometry_qualification_inherited=True,profile_calls=counts['profile_calls'],p4_passes=counts['p4_passes'],node_count=n+1,launch_speed_m_s=float(nodes[0]),minimum_nonlaunch_target_m_s=float(nodes[1:].min()),finish_target_m_s=float(nodes[-1]),positive_nonlaunch_targets=True,finish_is_free_positive_not_periodic_zero=True,discrete_forward_backward_qualified=discrete_ok,forward_q_residual_max=forward,backward_q_residual_max=backward,forward_q_violations=forward_bad,backward_q_violations=back_bad,engine_worst_endpoint_over1_segments=sum(x['engine_equivalent_ratio'] is not None and x['engine_equivalent_ratio']>1 for x in rows),engine_worst_endpoint_ratio_max=max(x['engine_equivalent_ratio'] or 0 for x in rows),aggregate_circle_over1_segments=sum(x['aggregate_translation_circle_ratio']>1 for x in rows),aggregate_circle_ratio_max=max(x['aggregate_translation_circle_ratio'] for x in rows),rear_equal_axle_drive_over1_segments=sum(x['rear_equal_axle_drive_circle_ratio'] is not None and x['rear_equal_axle_drive_circle_ratio']>1 for x in rows),rear_equal_axle_drive_ratio_max=max(x['rear_equal_axle_drive_circle_ratio'] or 0 for x in rows),sampled_projection_domain_errors=projection_errors,on_reference_cursor_mismatches=int(on_mismatch),off_reference_cursor_mismatches=int(off_mismatch),stale18_cursor_mismatches=int(stale_mismatch),maximum_sampled_cursor_arc_gap_m=max_arc_gap,maximum_stale_cursor_arc_gap_m=max_stale_gap,minimum_sampled_nonlocal_distance_gap_m=near_gap_min,off_reference_samples=n*6,on_reference_samples=n*2,off_reference_scope='Midpoint normal shifts ±0.25/1/3m plus generic rectangle exact tie and two unique one-sided projections. Finite synthetic diagnostics only, no tube continuity/tracking guarantee.',generic_nonlocal_projection_tie_and_jump_demonstrated=True,node_tangent_and_gradient_continuity_not_guaranteed=True,seam_L_sum_vs_cumsum_difference_m=float(ds.sum()-sarc[-1]),dynamic_safety_qualified=False,fresh_source_native_qualified=False,policy_AST_sha256=policysha,cursor_AST_sha256=hashlib.sha256(ast.dump(cursor_ast,include_attributes=False).encode()).hexdigest())
        status='EXECUTOR_INPUT_CANDIDATE_ONLY' if discrete_ok else 'EXECUTOR_INPUT_CANDIDATE_DISCRETE_LIMIT_UNQUALIFIED'
        check()
    except BaseException as e:
        status='TECHNICAL_INCONCLUSIVE';error=type(e).__name__+': '+str(e)
        q.write_json('stop.json',dict(state='STOPPED',error=error,counts=counts,traceback=traceback.format_exc()),control=True)
    finally:
        signal.setitimer(signal.ITIMER_PROF,max(.001,29-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,min(44-(time.perf_counter()-START),remain())))
        result=dict(stage=490,status=status,error=error,closure_receipt_required=True,counts=counts,summary=summary,resource=usage(),new_geometry_search_transform_interpolation_optimization=0,new_actual_world_reset_step_seed=0,new_second_condition=0,research_remaining=26175,reserve=84000,reserve_used=0,no_followup=True)
        q.write_json('result.json',result,control=True)
        try:
            entries=q.inventory()['files']
            for rec in entries:
                path=Path(rec['path']);b=path.read_bytes();assert b==path.read_bytes() and hashlib.sha256(b).hexdigest()==rec['sha256']
                if path.suffix=='.json':json.loads(b)
                if path.suffix=='.npz':
                    with np.load(io.BytesIO(b),allow_pickle=False) as z:
                        for key in z.files:assert np.isfinite(z[key]).all()
                rec['full_readbacks']=2
            q.write_json('retention-private.json',dict(files=entries,stage=490),exclusive=True)
            retained=q.inventory();check(closing=True);final=usage();closed=True
        except BaseException as closing_error:
            status='TECHNICAL_INCONCLUSIVE';error='490_CLOSURE:'+type(closing_error).__name__+': '+str(closing_error);closed=False
            q.write_json('stop.json',dict(state='CLOSURE_FAILED',error=error,counts=counts,resource=usage()),control=True)
            result.update(status=status,error=error,closure_failed=True,resource=usage());q.write_json('result.json',result,control=True)
            retained=q.inventory();final=usage()
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        print(json.dumps(dict(stage=490,status=status,error=error,closure_complete=closed,resource=final,retained_bytes=retained['bytes'],raw_files=retained['file_count'],summary=summary)),flush=True)

if __name__=='__main__':run(Path(sys.argv[1]))
