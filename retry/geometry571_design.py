"""Saved570-only primitive/error design; zero source integration."""
import json,math,time,os
from pathlib import Path
import numpy as np
from retry.clip561_core import atomic_write
from retry.geometry571 import active_component,component,vertices,layout
from retry.plan513_model import load_root
from retry.path569_design import sha

G=Path(__file__).resolve().parents[1];OLD=Path('/workspace/haic-response570-private');D=Path('/workspace/haic-response571-private');rd=lambda p:json.loads(p.read_text());SCALE=np.tile([.003,.03],34)

def constraints(V,JV,x,features,vertex_layout,observations,historical=None):
    q=[];J=[];L=[];keys=[];normals=[];floor=historical or {};ulp=np.abs(np.spacing(np.asarray(x,np.float32))).astype(float)
    for feature in features:
        raw=feature['raw'];normal=np.asarray(feature['normal']);offset=feature['offset'];poly=feature['polygon'];ids=vertex_layout[poly]
        for i in ids:
            value=float(V[raw,i]@normal-offset-.5);jac=normal@JV[raw,i];key=f"{raw}:{feature['kind']}:{poly}:{feature['feature']}:{i}";errors=[]
            for obs in observations:
                dx=np.asarray(obs['x'])-x;r=float(max(abs(dx/SCALE)))
                if r==0:continue
                actual=float(obs['V'][raw,i]@normal-offset-.5);optimism=max(0.,value+jac@dx-actual);errors.append(optimism/r)
            coeff=2*(max(errors,default=0.)+abs(jac)@ulp/.05+4*np.finfo(float).eps/.05);coeff=max(coeff,floor.get(key,0.));q.append(value);J.append(jac);L.append(coeff);keys.append(key);normals.append(normal)
    return np.asarray(q),np.asarray(J),np.asarray(L),keys

def main():
    D.mkdir(mode=0o700,exist_ok=False);cpu,wall=time.process_time(),time.perf_counter();static=rd(Path('/workspace/haic-response515-private/collected-map-state-private.json'));center=rd(OLD/'proposal-2-0-diagnostic-private.json');roots=[load_root(dict(r['root_without_roads'],roads=static['root']['roads'])) for r in center['rows']];V=np.stack([vertices(r) for r in roots]);vl=layout(roots[0]);nverts=V.shape[1];assert len(center['rows'])==134
    features=[]
    # Frozen rule: failing hold145 and its predecessor144, raws573..580.
    for global_raw in range(573,581):
        i=global_raw-529;f=active_component(roots[i],static);f['raw']=i;features.append(f)
    evidence=[];observations=[]
    for name in ['cal-4-0','cal-4-1','proposal-3-0-diagnostic','proposal-3-1-diagnostic']:
        data=rd(OLD/(name+'-private.json'));vv=np.stack([vertices(load_root(dict(r['root_without_roads'],roads=static['root']['roads']))) for r in data['rows']]);observations.append(dict(x=np.asarray(data['x']),V=vv,label=name))
        if name.startswith('proposal'):
            row=data['rows'][48];root=load_root(dict(row['root_without_roads'],roads=static['root']['roads']));f=active_component(root,static);evidence.append(dict(label=name,global_raw=577,kind=f['kind'],polygon=f['polygon'],feature=f['feature'],exact_gap=row['margin'],component_gap=f['gap']))
    fd=np.empty((68,134,nverts,2));seen=np.zeros((68,134),bool)
    with open(OLD/'raw-journal-private.jsonl') as file:
        for line in file:
            r=json.loads(line)
            if r['kind']!='AFTER_TICK':continue
            context=r['context'];label=context['label']
            if not label.startswith('FD-4-'):continue
            j=int(label.split('-')[-1]);i=context['global_raw']-528;root=load_root(dict(r['root'],roads=static['root']['roads']));fd[j,i]=vertices(root);seen[j,i]=True
    assert np.all(seen);linear=rd(OLD/'linear-4-private.json');steps=np.asarray(linear['steps']);assert all(x is not None for x in steps);JV=np.moveaxis((fd-V[None,:,:,:])/steps[:,None,None,None],0,-1)
    q,J,L,keys=constraints(V,JV,np.asarray(center['x']),features,vl,observations);assert min(q)>=0 and np.all(np.isfinite(L)) and np.all(L>=0)
    root=roots[48];seed_component=active_component(root,static);critical=[k for k in range(len(keys)) if keys[k].startswith('48:')];critical_min=int(min(critical,key=lambda i:q[i]));n=np.asarray(next(f for f in features if f['raw']==48)['normal']);details=[]
    for obs in observations:
        dx=obs['x']-center['x'];r=max(abs(dx/SCALE));feature=next(f for f in features if f['raw']==48);ids=vl[feature['polygon']];actual=np.asarray([obs['V'][48,i]@n-feature['offset']-.5 for i in ids]);pred=q[critical]+J[critical]@dx
        details.append(dict(label=obs['label'],normalized_displacement=float(r),support_slack_min=float(min(actual)),positive_support_optimism_max=float(max(np.maximum(0,pred-actual))),derived_error_allowance_max=float(max(L[critical])*r)))
    np.savez_compressed(D/'vertex-sensitivity-private.npz',V=V,JV=JV,observation_vertices=np.stack([o['V'] for o in observations]),observation_controls=np.stack([o['x'] for o in observations]));os.chmod(D/'vertex-sensitivity-private.npz',0o600)
    with open(D/'vertex-sensitivity-private.npz','rb') as f:os.fsync(f.fileno())
    atomic_write(D/'primitive-design-private.json',dict(center_x=center['x'],features=features,vertex_layout=vl,keys=keys,coefficients=L,seed_support_slacks=q,observation_labels=[o['label'] for o in observations]))
    out=dict(passed=True,method='Keep all68full-command objective. Add frozen signed separating support for each vertex of the active polygon,for each raw in failinghold145andprecedinghold144. Original full exactgeometry validator unchanged.',evidence=evidence,seed_component=dict(kind=seed_component['kind'],polygon=seed_component['polygon'],feature=seed_component['feature'],gap=seed_component['gap']),support_constraints=len(q),minimum_seed_support_slack=float(min(q)),seed_included=True,critical_raw577_error_profiles=details,critical_coefficient_max_m_per_normalized_step=float(max(L[critical])),coefficient_rule='Twice max positive signed-vertex prediction optimism divided by ACTUAL normalized displacement across savedcal2+savedreject2,plus propagatedfloat32ULP and fourbinary64eps per .05. Zero-step L*t=0. No fixedbuffer grid,epsilon rounding or coefficient clipping. Historical measured coefficient floor retained;new rejected directions update by same rule only within registered restoration cap.',scope='A signed support halfspace is sufficient for separating that polygon from that roadsegment/circle;all vertices,not just the previous minimizer. It is not a certificate for other components or road-union coverage. Source exactwholevehicle validator always rechecks. Empirical errors are not universalbounds.',source_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,input_sha256={str(p):sha(p) for p in [OLD/'raw-journal-private.jsonl',OLD/'linear-4-private.json',OLD/'proposal-2-0-diagnostic-private.json',OLD/'proposal-3-0-diagnostic-private.json',OLD/'proposal-3-1-diagnostic-private.json']},private_cache_sha256=sha(D/'vertex-sensitivity-private.npz'))
    atomic_write(G/'retry/geometry571_design.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':main()
