"""Stored568-only capsule/vector design checks. No simulator calls."""
import hashlib,json,math,time
from pathlib import Path
import numpy as np
from retry.clip561_core import atomic_write

G=Path(__file__).resolve().parents[1];OLD=Path('/workspace/haic-response568-private');D=Path('/workspace/haic-response569-private')
rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def capsule(points,a,b):
    p=np.asarray(points);a=np.asarray(a);b=np.asarray(b);v=b-a;u=np.sum((p-a)*v,axis=-1)/np.sum(v*v,axis=-1);q=a+np.clip(u,0,1)[...,None]*v;r=p-q;dist=np.linalg.norm(r,axis=-1)
    return dist,r,u,q

def project_all(p,previous,path):
    a=np.asarray(path['points']);b=np.roll(a,-1,axis=0);v=b-a;l=np.linalg.norm(v,axis=1)
    u=np.clip(np.sum((p[:,None,:]-a)*v,axis=2)/(l*l),0,1);q=a+u[...,None]*v;distance=np.linalg.norm(p[:,None,:]-q,axis=2);s=np.asarray(path['arcs'][:-1])+u*l;s+=np.rint((previous[:,None]-s)/path['length'])*path['length'];eligible=(s>=previous[:,None]-5)&(s<=previous[:,None]+30)
    index=np.argmin(np.where(eligible,distance,np.inf),axis=1);assert np.all(np.any(eligible,axis=1));j=np.arange(len(p));return index,distance[j,index],eligible,u[j,index],q[j,index],v[index]/l[index,None]

def seed_g(rows,prior):
    g=[]
    for row in rows:
        delta=row['progress']-prior['progress'];lim=max(5.,2*math.dist(row['root_without_roads']['center'],prior['root_without_roads']['center']))
        g.extend([row['margin']-.5,3-row['path_error'],4.85-row['reference_overspeed'],*[1.059-f['ratio'] for f in row['forces']],100-row['body'],delta+.5,lim-delta]);prior=row
    return np.array(g)

def envelopes(seed,linear,patterns):
    errors=[];rerrors=[];oerrors=[];perrors=[];radius=.05
    for ev in patterns:
        dx=np.asarray(ev['x'])-seed['x'];errors.append(np.maximum(0,seed['g']+linear['J']@dx-ev['g']));rerrors.append(np.maximum(0,np.asarray(ev['ratios'])-seed['ratios']-linear['R']@dx));oerrors.append(np.maximum(0,seed['order']+linear['O']@dx-ev['order']));perrors.append(np.linalg.norm(seed['P']+np.einsum('ijk,k->ij',linear['P'],dx)-ev['P'],axis=1))
    ulp=np.abs(np.spacing(seed['x'].astype(np.float32))).astype(float);floor=4*np.finfo(float).eps
    lg=2*(np.max(errors,axis=0)+abs(linear['J'])@ulp+floor)/radius;lr=2*(np.max(rerrors,axis=0)+abs(linear['R'])@ulp+floor)/radius;lo=2*(np.max(oerrors,axis=0)+abs(linear['O'])@ulp+floor)/radius
    lp=2*(np.max(perrors,axis=0)+np.linalg.norm(np.einsum('ijk,k->ij',abs(linear['P']),ulp),axis=1)+floor)/radius
    return dict(g=lg,ratio=lr,order=lo,position=lp,rule='Step-dependent empirical first-order error envelope L*t; t>=normalized infinity displacement, radius<=.05. No fixed positive target at zero step, no clipping of coefficients. Not a universal error bound.')

def main():
    D.mkdir(mode=0o700,exist_ok=True)
    if (D/'stored-model-private.json').exists():raise RuntimeError('SAVED_DESIGN_ALREADY_COMPLETED')
    cpu,wall=time.process_time(),time.perf_counter();path=rd(Path('/workspace/haic-response551-private/frozen-paths-private.json'))['candidate'];tape=rd(Path('/workspace/haic-response565-private/final-tape-private.json'));rows=tape['rows'][528:];prior=tape['rows'][527]
    p0=np.asarray([r['root_without_roads']['center'] for r in rows]);prev0=np.asarray([prior['progress']]+[r['progress'] for r in rows[:-1]]);idx,dist,eligible,u,q,tangent=project_all(p0,prev0,path);a=np.asarray(path['points'])[idx];b=np.roll(np.asarray(path['points']),-1,axis=0)[idx]
    assert np.max(abs(dist-np.asarray([r['path_error'] for r in rows])))<1e-9
    cases={}
    with open(OLD/'raw-journal-private.jsonl') as f:
        for line in f:
            r=json.loads(line)
            if r['kind']=='AFTER_TICK':
                current_case=r['context']['label'];cases.setdefault(current_case,dict(P=[],progress=[],distance=[]))['P'].append(r['root']['center'])
            elif r['kind']=='RAW_VERDICT':
                case=cases[current_case];case['progress'].append(r['progress']);case['distance'].append(r['path_error'])
    checks=dict(exact_source_distance_match=True,signed_equals_distance_for_interior=True,frozen_capsule_upperbounds_source_when_eligible=True);stats=dict(raws=0,nearest_segment_changes=0,frozen_ineligible=0,interior=0,endpoints=0,signed_underestimates_endpoint=0,centerline_side_changes=0,curved_seed_segments=0)
    pts=np.asarray(path['points']);turn=[]
    for i in idx:
        v=pts[i]-pts[(i-1)%len(pts)];w=pts[(i+1)%len(pts)]-pts[i];turn.append(abs(math.atan2(v[0]*w[1]-v[1]*w[0],v@w)))
    stats['curved_seed_segments']=sum(x>.01 for x in turn);seed_signed=tangent[:,0]*(p0-q)[:,1]-tangent[:,1]*(p0-q)[:,0]
    for name,c in cases.items():
        p=np.asarray(c['P']);previous=np.asarray([prior['progress']]+c['progress'][:-1]);ii,dd,ee,uu,qq,tt=project_all(p,previous,path);cd,res,fu,fq=capsule(p,a,b);signed=tangent[:,0]*(p-a)[:,1]-tangent[:,1]*(p-a)[:,0];interior=(fu>=0)&(fu<=1);feligible=ee[np.arange(134),idx]
        checks['exact_source_distance_match'] &= bool(np.max(abs(dd-c['distance']))<1e-9);checks['signed_equals_distance_for_interior'] &= bool(np.max(abs(abs(signed[interior])-cd[interior]))<1e-9);checks['frozen_capsule_upperbounds_source_when_eligible'] &= bool(np.all(cd[feligible]+1e-9>=dd[feligible]))
        stats['raws']+=len(p);stats['nearest_segment_changes']+=int(sum(ii!=idx));stats['frozen_ineligible']+=int(sum(~feligible));stats['interior']+=int(sum(interior));stats['endpoints']+=int(sum(~interior));stats['signed_underestimates_endpoint']+=int(sum((~interior)&(cd>abs(signed)+1e-9)));stats['centerline_side_changes']+=int(sum(seed_signed*signed<0))
        c['P']=p
    # Analytic endpoint counterexample, anchored to a stored segment.
    v=(b[0]-a[0]);v=v/np.linalg.norm(v);outside=b[0]+3.1*v;dc,_,_,_=capsule(outside,a[0],b[0]);assert abs(float(dc)-3.1)<1e-9
    steps=np.asarray(rd(OLD/'linearization-01-private.json')['steps']);rawlin=rd(OLD/'linearization-01-private.json');linear={k:np.asarray(rawlin[k]) for k in ['J','R','O','T']};linear['P']=np.stack([(cases[f'FD-01-{j:02d}']['P']-p0)/steps[j] for j in range(40)],axis=2)
    x0=np.array([v for item in tape['commands'] if 133<=item['index']<=152 for v in [item['action'][0],item['action'][1]-item['action'][2]]]);seed=dict(x=x0,g=seed_g(rows,prior),ratios=np.asarray([f['ratio'] for row in rows for f in row['forces']]),order=np.asarray(rd(OLD/'FD-01-00-private.json')['order']),P=p0)
    from retry.clip561_core import prefix_slacks
    seed['order']=prefix_slacks(seed['ratios'],64,1728);patterns=[]
    for n in range(2):
        ev=rd(OLD/f'calibration-{n}-private.json');ev['P']=cases[f'calibration-{n}']['P'];patterns.append(ev)
    env=envelopes(seed,linear,patterns);labels=rd(OLD/'FD-01-00-private.json')['labels'];keep=np.array(labels)!='path';seed_ok=bool(np.all(seed['g'][keep]>=0) and np.all(seed['order']>=0) and np.all(dist<=3))
    # Every model tightening is L*t, with t=0 at the exact float32 seed.
    checks.update(exact_feasible_seed_included=seed_ok,all_envelope_coefficients_finite_nonnegative=all(np.all(np.isfinite(env[k])) and np.all(env[k]>=0) for k in ['g','ratio','order','position']),path_radius_nonnegative_at_seed=True,endpoint_signed_only_counterexample_detected=True)
    upper={'path_radius':3.,'force_slack':1.059,'body_slack':100.,'reference_slack':84.85,'clipping_rank_slack':1.}
    out=dict(passed=all(checks.values()),checks=checks,stats=stats,representation='Exact distance to frozen finite seed segment (capsule), evaluated through 2D affine position, with cutting-plane LP and exact convex-model capsule recheck. Signed lateral is only equivalent when projection is interior.',equivalence='For any eligible fixed segment, capsule distance bounds the minimum eligible polyline distance from above. Equality holds when it is an actual minimizer. Segment changes may make the model conservative. If the fixed segment becomes ineligible under previous-progress window, this implication is not asserted; exact original source projection and gates recheck every proposal.',curve_and_endpoint='Curved polyline is a union of segment capsules, not one infinite strip. Fixed capsule supports endpoints and centerline crossing. Infinite-line signed lateral alone underestimates endpoint distance; stored segment endpoint+3.1 tangent is a counterexample.',error_rule=env['rule'],universal_upper_bounds=upper,other_constraints='All scalar physical/force/rank tightenings also use L*t, never a fixed positive margin. Zero-step seed is feasible exactly. LP explicitly bounds attainable tightenings and model predictions for known universal limits; finite local-box attainable upper bounds are recorded for every row. Footprint scalar errors remain large and are separately tracked, not clipped or asserted smooth.',position_calibration_error_max_m=float(max(env['position'])*.05/2),footprint_coefficient_max=float(max(env['g'][np.array(labels)=='footprint'])),model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,inputs_sha256={str(p):sha(p) for p in [OLD/'raw-journal-private.jsonl',OLD/'linearization-01-private.json',OLD/'calibration-0-private.json',OLD/'calibration-1-private.json']})
    atomic_write(D/'stored-model-private.json',dict(seed=seed,linear=linear,envelope=env,a=a,b=b,indices=idx,labels=labels));atomic_write(G/'retry/path569_design.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':main()
