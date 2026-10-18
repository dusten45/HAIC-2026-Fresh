import json,time,math,numpy as np
from pathlib import Path
from retry.braking526_control import path_for
from retry.plan513_model import load_root,polygons
from retry.path521_control import obstacle_clearances
from retry.brake506_geometry import point_segment
cpu=time.process_time();wall=time.perf_counter();s=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());p=path_for(s,'candidate');c=np.array([(z[2],z[3]) for z in s['track']]);pts=np.array(p['points']);ds=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1);a=np.array(p['arcs'][:-1]);L=p['length'];k=np.array(p['curvature']);r=load_root(s['root']);body=np.concatenate([np.array(poly) for poly in polygons(r)])-r.center
near=np.array([min(np.linalg.norm(x-np.array(z),axis=1)) for z,_ in s['obstacles'] for x in [pts]])
obsdist=np.array([min(math.dist(x,z)-rad for z,rad in s['obstacles']) for x in pts]);turn=np.abs(k)*np.array(p['ds']);mask=obsdist<20
boundary=np.array(s['boundary']);width=np.array([min(point_segment(x,*edge) for edge in s['boundary']) for x in c]);origin=np.array(s['root']['center']);vel=np.array(r.planar.linear.velocity);angle=r.planar.angle;local=body@np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
tr=json.loads(Path('/workspace/haic-response528-private/cold-candidate-model-private.json').read_text())['trace'];clipped=sum(z['clipped'] for row in tr for z in row['forces']);minrow=min(tr,key=lambda x:x['margin']);peakrow=max(tr,key=lambda x:max(y['ratio'] for y in x['forces']));curve=int(np.argmax(abs(k)));obsi=int(np.argmin(obsdist))
# all station ids and coordinates stay private
risks=[]
for label,node in [('obstacle',obsi),('curvature',curve)]:
 target=max(0.,a[node]-35.);j=min(range(len(tr)),key=lambda j:abs(tr[j]['progress']-target));hold=tr[j]['index'];before=load_root(s['root']) if hold==1 else load_root(dict(next(z['root_without_roads'] for z in tr if z['index']==hold-1 and z['raw']==4),roads=s['root']['roads']));previous=[z for z in tr if z['index']<hold and z['index']>24];hist=dict(clipped=sum(w['clipped'] for z in previous for w in z['forces']),samples=4*len(previous));risks.append(dict(label=label,index=hold,node=node,root_without_roads=(s['root'] if hold==1 else next(z['root_without_roads'] for z in tr if z['index']==hold-1 and z['raw']==4)),progress=0 if hold==1 else next(z['progress'] for z in tr if z['index']==hold-1 and z['raw']==4),history=hist,holds=24))
out=dict(centerline_length_m=float(ds.sum()),Gaussian_length_m=L,Gaussian_extra_length_m=L-float(ds.sum()),Gaussian_max_abs_curvature=float(max(abs(k))),Gaussian_curvature_squared_integral=float(sum(k*k*np.array(p['ds']))),Gaussian_abs_turn_rad=float(turn.sum()),obstacle_20m_fraction_nodes=float(mask.mean()),obstacle_20m_abs_turn_rad=float(turn[mask].sum()),Gaussian_min_obstacle_centerline_clearance_m=min(obstacle_clearances(pts,s['obstacles'])),centerline_min_boundary_distance_m=float(width.min()),centerline_max_boundary_distance_m=float(width.max()),nominal_footprint_local_min=local.min(axis=0).tolist(),nominal_footprint_local_max=local.max(axis=0).tolist(),nominal_footprint_circumradius_m=float(np.linalg.norm(body,axis=1).max()),saved528_max_path_error_m=max(x['path_error'] for x in tr),saved528_min_margin_m=minrow['margin'],saved528_clip_count=clipped,analysis_CPU_s=time.process_time()-cpu,analysis_wall_s=time.perf_counter()-wall,model_ticks=0,force_evaluations=0,native_actions=0,risks_selected_before_design=['obstacle','curvature'])
for file,data in [('/workspace/HAIC-2026-Fresh/retry/line530_analysis.json',out),('/workspace/haic-response530-private/risks-private.json',risks)]:
 with open(file,'x') as f:json.dump(data,f,indent=2)
print(json.dumps(out,indent=2))
