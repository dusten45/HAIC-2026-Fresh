"""Read-only current240 bottleneck evidence; no native, model rollout or candidate.

GT trajectory/fixture/wheel states are diagnostic only. Endpoint-adjusted time
bins are derived from current records, not stage235's older232 policy.
"""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np


def first_tick_force(snapshot,command):
    # Exact source first-Car.step algebra before its Box2D solve, not a rollout.
    limits={r['idx']:r['friction'] for r in snapshot['roads']};damage=snapshot['damage'];engine=max(.8,1-damage*.25);grip=max(.6,1-damage*.5);ratios=[]
    for i,w in enumerate(snapshot['wheels']):
        angle=w['body']['angle'];velocity=np.asarray(w['body']['velocity']);forward=np.array([-np.sin(angle),np.cos(angle)]);side=np.array([np.cos(angle),np.sin(angle)]);vf=float(velocity@forward);vs=float(velocity@side);omega=w['dynamics']['omega'];gas=w['dynamics']['gas']
        if i>=2:gas+=min(.1,float(command[1])-gas)
        omega+=.02*40000*engine*gas/1.6/(abs(omega)+5)
        if command[2]>=.9:omega=0.
        elif command[2]>0:omega-=np.sign(omega)*min(15*float(command[2]),abs(omega))
        f=(omega*.54-vf)*82;p=-vs*82;limit=max([400*snapshot['grass_friction_multiplier']]+[400*limits[k] for k in w['tiles']])*grip
        ratios.append(float(np.hypot(f,p)/limit))
    return ratios


def audit(root,out):
    start,cpu=time.perf_counter(),time.process_time();roads=[];hashes={};reference=json.loads((root/'stage251/plan.json').read_text())['references']
    for road in ['O0','O2','N0','N1','N2','N3']:
        folder=root/'stage251/training'/road;q=folder/'materialized.json';m=json.loads(q.read_text());z=np.load(folder/'cache-private.npz');f=z['features'];a=z['commands'];actual=m['actual'];speed=np.array([r['speed_m_s'] for r in actual]);t0=m['snapshots']['1']['actual_time'];elapsed=np.array([r['time']-t0 for r in actual]);elapsed[-1]=reference[road]['lap_ms']/1000;dt=np.diff(np.r_[0,elapsed]);assert (dt>=0).all()
        missing=f[:,0]>0;near=f[:,8]>0;small=np.abs(f[:,5])<.01;low=speed<35;quiet=small&~near&~missing;position=np.array([r['position'] for r in actual]);positions=np.r_[[m['snapshots']['1']['hull']['position']],position];distance=float(np.linalg.norm(np.diff(positions,axis=0),axis=1).sum());tiles=sorted(m['snapshots']['1']['roads'],key=lambda x:x['idx']);centers=np.array([np.mean(r['fixture']['geometry']['vertices'],axis=0) for r in tiles]);loop=float(np.linalg.norm(np.diff(np.r_[centers,centers[:1]],axis=0),axis=1).sum());launch=first_tick_force(m['snapshots']['4'],a[3])
        masks=dict(target_missing=missing,near_hazard=near,small_pixel_curvature=small,low_speed=low,low_small_curvature_no_hazard=low&quiet,brake_above_point05_small_curvature_no_hazard=quiet&(a[:,2]>.05),both_pedals_above_point05=(a[:,1]>.05)&(a[:,2]>.05))
        roads.append(dict(road=road,current240_lap_s=reference[road]['lap_ms']/1000,time_bins_s={k:float(dt[v].sum()) for k,v in masks.items()},actual_path_over_tile_center_loop=distance/loop,speed_quantiles_m_s=np.percentile(speed,[5,50,95]).tolist(),initial4_pixel_curvature_abs_max=float(np.abs(f[:4,5]).max()),initial4_near_hazard_count=int(near[:4].sum()),preaction4_rear_force_over_friction_limit=launch[2:],force_scope='Sourcealgebra firstphysics tick atstoredactualboundary4, beforeBox2Dsolve; not entirelaunch/speedgain prediction.'))
        hashes[str(q)]=hashlib.sha256(q.read_bytes()).hexdigest();hashes[str(folder/'cache-private.npz')]=hashlib.sha256((folder/'cache-private.npz').read_bytes()).hexdigest()
    result=dict(stage=254,policy='Current240 exactstage251 materializations; noolder232bottleneck reuse',roads=roads,bin_definitions=dict(small_pixel_curvature='abs(feature5)<.01 diagnosticpixelrouteproxy, notGTroadcurvature',low_speed='postaction speed<35m/s; descriptive, not a runtime threshold',bins_overlap=True,time='Stepelapsed weights, finalboundaryadjustedtoofficiallap',path_ratio='Actualhullpolyline / loopthroughroadtilefixturecentroids; approximatepathproxy, not shortestfeasiblelap'),decision='No justified untestedcandidate selected. Persistentstraightlow-speed/pathinflation/targetloss notobserved. Simultaneouspedals alone isnotcausalproof; globalexclusion failed236. Initialrearforce alreadyclamped makes gas-only launch increase unsupported.',minimum_next_observation='Useexistingfullquery-boundary states/sourceforcealgebra toseparate longitudinal versus lateral traction saturation and counteracting wheel forces in longstraight-braking segments beforeanynew actualpulse. No new fullroad/decoder/teacher dataset is required for that first diagnostic.',native_actions=0,model_physics_ticks=0,new_candidates=0,source_cache_sha256=hashes,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu)
    with out.open('x') as h:json.dump(result,h,indent=2);h.write('\n')
    out.chmod(0o600);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps({k:v for k,v in audit(a.root,a.output).items() if k!='source_cache_sha256'}))
