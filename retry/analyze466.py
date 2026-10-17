"""466 saved-only reference projection and co-located force proxies. No physics."""
import hashlib,json,math,shutil,time
from pathlib import Path
import numpy as np
from retry.signed417_executor import canonical_projection
from retry.scalar392_audit import pedals

def project_four(nodes,ds,model):
    v=np.asarray(nodes,float).copy();ds=np.asarray(ds,float)
    for _ in range(4):
        for i in range(len(ds)-1,-1,-1):v[i]=min(v[i],math.sqrt(v[i+1]**2+2*model['brake_accel']*ds[i]))
        for i in range(len(ds)):
            a=min(model['rear_traction_accel'],80000/(v[i]+2.7)/model['effective_mass'])
            v[i+1]=min(v[i+1],math.sqrt(v[i]**2+2*a*ds[i]))
    return v

def segment_proxy(q0,q1,k0,k1,distance,m):
    dq=q1-q0;dk=k1-k0;a=dq/(2*distance);where=[0.,1.]
    if dq*dk:
        u=-(q0*dk+dq*k0)/(2*dq*dk)
        if 0<u<1:where.append(u)
    at=max(where,key=lambda u:abs((q0+dq*u)*(k0+dk*u)))
    fy=m['mass']*(q0+dq*at)*(k0+dk*at);fx=m['mass']*a
    rear_mass=m['mass']+(m['effective_mass']-m['mass'])/2
    rear=math.hypot(rear_mass*max(a,0),fy/2)/800 if a>0 else None
    engine=m['effective_mass']*max(a,0)*(math.sqrt(max(q0,q1))+2.7)/80000 if a>0 else None
    leftA=min(m['rear_traction_accel'],80000/(math.sqrt(q0)+2.7)/m['effective_mass'])
    return dict(accel=a,max_lateral_force_abs_N=abs(fy),lateral_witness_fraction=at,
        aggregate_translation_circle_ratio=math.hypot(fx,fy)/1600,
        rear_equal_axle_drive_circle_ratio=rear,engine_equivalent_ratio=engine,
        discrete_forward_q_residual=q1-q0-2*leftA*distance,
        discrete_backward_q_residual=q0-q1-2*m['brake_accel']*distance)

def clock_at(s,nodes,ds):
    arcs=np.r_[0,np.cumsum(ds)];assert 0<=s<=arcs[-1];clock=0.
    for i,length in enumerate(ds):
        take=min(length,max(0,s-arcs[i]))
        if take:
            r=math.sqrt(nodes[i]**2+(nodes[i+1]**2-nodes[i]**2)*take/length)
            clock+=2*take/(nodes[i]+r)
    return clock

def point_terms(fixed,nodes,row):
    z=canonical_projection(fixed['line'],row['pre']['pos'],row['pre']['vel'],'FIRST_LAP');j,u=z['index'],z['u'];r=math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2)
    if not r>0:raise ValueError('reference_zero')
    f=(nodes[j+1]**2-nodes[j]**2)/(2*fixed['free_profile']['ds'][j]);ff=f*z['sigma']/r;feedback=1.5*(r-row['pre']['speed']);p=pedals(ff+feedback,row['pre']['speed'],fixed['model'])
    return dict(arc=z['arc'],target=r,gradient=f,ff=ff,feedback=feedback,raw=ff+feedback,command_accel=p['command_accel'],gas=p['gas'],brake=p['brake'])

def run(root,output_name='stage466'):
    cpu,wall=time.process_time(),time.perf_counter();g=Path(__file__).resolve().parents[1];manifest={}
    def read(path,lines=False):
        raw=path.read_bytes();manifest[str(path)]=hashlib.sha256(raw).hexdigest()
        return [json.loads(s) for s in raw.splitlines()] if lines else json.loads(raw)
    oldplan=read(root/'stage465-plan-durable-private.json');ledger=read(root/'project-effective-budget-v475.json')
    assert ledger['research_remaining']==26346 and ledger['final_reserved_actions']==84000 and ledger['final_reserve_used']==0
    for group in ['protected','original408_preserve']:
        for path,h in oldplan[group].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h
    fixed=read(Path(oldplan['fixed_plan']));pace=np.asarray(read(Path(oldplan['pace_path']))['frozen268']);original=np.asarray(fixed['free_profile']['speed'])*pace;ds=np.asarray(fixed['free_profile']['ds']);k=np.r_[fixed['free_profile']['curvature'],fixed['free_profile']['curvature'][0]];m=fixed['model'];projected=project_four(original,ds,m);arcs=np.r_[0,np.cumsum(ds)];L=arcs[-1]
    assert original[0]==projected[0]==0 and np.all(projected<=original) and np.all(projected[1:]>0)
    per={};summaries={}
    for name,nodes in [('Original',original),('Projected4',projected)]:
        rows=[segment_proxy(nodes[i]**2,nodes[i+1]**2,k[i],k[i+1],ds[i],m) for i in range(len(ds))];per[name]=rows
        summaries[name]=dict(reference_clock_s=clock_at(L,nodes,ds),gradient_min=min(r['accel'] for r in rows),gradient_max=max(r['accel'] for r in rows),
            aggregate_translation_proxy_over1_segments=sum(r['aggregate_translation_circle_ratio']>1 for r in rows),aggregate_translation_proxy_max=max(r['aggregate_translation_circle_ratio'] for r in rows),
            rear_equal_axle_drive_proxy_over1_segments=sum(r['rear_equal_axle_drive_circle_ratio'] is not None and r['rear_equal_axle_drive_circle_ratio']>1 for r in rows),rear_equal_axle_drive_proxy_max=max(r['rear_equal_axle_drive_circle_ratio'] or 0 for r in rows),
            continuous_engine_equivalent_over1_segments=sum(r['engine_equivalent_ratio'] is not None and r['engine_equivalent_ratio']>1 for r in rows),continuous_engine_equivalent_ratio_max=max(r['engine_equivalent_ratio'] or 0 for r in rows),
            discrete_forward_q_residual_max=max(r['discrete_forward_q_residual'] for r in rows),discrete_backward_q_residual_max=max(r['discrete_backward_q_residual'] for r in rows),
            discrete_forward_over_tolerance=sum(r['discrete_forward_q_residual']>1e-8 for r in rows),discrete_backward_over_tolerance=sum(r['discrete_backward_q_residual']>1e-8 for r in rows),interior_lateral_max_witness_segments=sum(0<r['lateral_witness_fraction']<1 for r in rows))
    paths=dict(P442=root/'stage442/actual_P/trace-private.jsonl',P458=root/'stage458/actual_P/trace-private.jsonl',PulseOnce463=root/'stage463-native/actual_SecantOnce/trace-private.jsonl');observed={};rootrow=None;originoffset=None;actualtyres=[]
    for label,path in paths.items():
        rows=read(path,True);changes=oldbrake=newbrake=commonbrake=qualified=0;friction=[];clip=0
        for row in rows:
            actualtyres.extend(row['raw_tire_samples']);friction.extend(t['friction_limit'] for t in row['raw_tire_samples']);clip+=sum(t['clipped'] for t in row['raw_tire_samples'])
            if row['nominal_memory_after']['C']['phase']!='FIRST_LAP' or not 0<row['progress_before']<L:continue
            old=point_terms(fixed,original,row);new=point_terms(fixed,projected,row);qualified+=1
            cmd=np.asarray(row['nominal'],np.float32).copy();cmd[1:]=[new['gas'],new['brake']]
            changes+=not np.array_equal(cmd,np.asarray(row['nominal'],np.float32))
            oldbrake+=row['pre']['speed']<old['target'] and old['raw']<0
            newbrake+=row['pre']['speed']<new['target'] and new['raw']<0
            commonbrake+=row['pre']['speed']<old['target'] and new['raw']<0
        observed[label]=dict(qualified_saved_states=qualified,counterfactual_pedal_changes=int(changes),old_under_own_target_braking=int(oldbrake),projected_under_own_target_braking=int(newbrake),projected_braking_below_original_target=int(commonbrake),observed_friction_limit_min=min(friction),observed_friction_limit_max=max(friction),observed_clipped_wheel_samples=clip)
        if label=='P458':rootrow=rows[125];originoffset=rows[22]['progress_before']
    old=point_terms(fixed,original,rootrow);new=point_terms(fixed,projected,rootrow);s=new['arc'];v=rootrow['pre']['speed'];future=[(arc-s,target) for arc,target in zip(arcs,projected) if arc>s]
    ceiling=min(math.sqrt(target**2+2*m['brake_accel']*distance) for distance,target in future)
    lower=[(d,target) for d,target in future if target<v];debt=max(((v*v-target*target)/(2*d)/m['brake_accel'] for d,target in lower),default=0.)
    root_binding=dict(native_pre_step=126,current_speed_m_s=v,original={key:old[key] for key in ['target','gradient','ff','feedback','raw','command_accel']},projected={key:new[key] for key in ['target','gradient','ff','feedback','raw','command_accel']},
        current_speed_below_projected_target=v<=new['target'],discrete_backward_join_ceiling_m_s=ceiling,current_speed_below_backward_join_ceiling=v<=ceiling,root_max_required_brake_over_B=debt,exact_physical_join_qualified=False,reference_remaining_clock_s=dict(Original=clock_at(L,original,ds)-clock_at(s,original,ds),Projected4=clock_at(L,projected,ds)-clock_at(s,projected,ds)))
    boundaries=[0,60,120,180,240,270,330,390,450,510,570,630,690,750];bins=[]
    for lo,hi in zip(boundaries,boundaries[1:]+[L-originoffset]):
        a,b=originoffset+lo,originoffset+hi;ids=[i for i in range(len(ds)) if a<=(arcs[i]+arcs[i+1])/2<b]
        bins.append(dict(from_pre23_m=[lo,hi],old_clock_s=clock_at(b,original,ds)-clock_at(a,original,ds),projected_clock_s=clock_at(b,projected,ds)-clock_at(a,projected,ds),segments=len(ids),changed_gradient_segments=sum(per['Original'][i]['accel']!=per['Projected4'][i]['accel'] for i in ids)))
    sourcefiles=['retry/analyze466.py','retry/static466.py','retry/racing258_plan.py','retry/racing258_run.py','retry/pace268_profile.py','retry/signed417_executor.py','retry/scalar392_audit.py','core/vendor/car_dynamics.py','retry/receipt421_io.py','retry/loss389_analyze.py','retry/observer435.py','retry/pilot433_meter.py','retry/capture434.py','retry/pilot420_json.py','retry/terminal410_run.py']
    sources={}
    for rel in sourcefiles:
        path=g/rel;h=hashlib.sha256(path.read_bytes()).hexdigest();sources[rel]=h;manifest[str(path)]=h
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in manifest.items())
    assert output_name in ['stage466','stage466-numeric-recovery1']
    d=root/output_name;assert not d.exists();d.mkdir(mode=0o700)
    def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n');path.chmod(0o600)
    save(d/'projection-and-segments-private.json',dict(original_nodes=original.tolist(),projected_nodes=projected.tolist(),segments=per));save(d/'input-sha256-private.json',manifest)
    result=dict(stage=466,status='PURE_NUMERIC_AND_COMPRESSION_CODE_REVIEW_ONLY',new_physics_native_world_reset_seed_learning_HOLDOUT_SEALED_reserve_paid=0,compression_implementation_executed=False,source_hashes=sources,private_input_manifest_sha256=hashlib.sha256((d/'input-sha256-private.json').read_bytes()).hexdigest(),profile_summaries=summaries,node_count=len(original),segment_count=len(ds),nodes_changed=int(sum(projected!=original)),gradient_segments_changed=sum(a['accel']!=b['accel'] for a,b in zip(per['Original'],per['Projected4'])),exactly_four_passes=True,verification_q_roundoff_tolerance=1e-8,spatial_bins=bins,root_binding=root_binding,saved_state_counterfactuals=observed,all_proxy_assumptions='piecewise-linear squared speed; linearly interpolated signed path curvature; translation Fx=M*a; equal-axle rear Fx=(M+2I/r²)*a; engine Meff*a separate; allroad/grip1 nominal400N/wheel; no exact tyre feasibility',protected_files_verified=18,ledger475_unchanged=True,research_remaining=26346,reserve=84000,reserve_used=0,target11_seconds_unchanged=True,storage={volume:dict(free=shutil.disk_usage(volume).free,total=shutil.disk_usage(volume).total) for volume in ['/tmp','/workspace']},CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    result=json.loads(json.dumps(result,default=lambda x:x.item() if isinstance(x,np.generic) else x))
    save(d/'result-private.json',result);return result
