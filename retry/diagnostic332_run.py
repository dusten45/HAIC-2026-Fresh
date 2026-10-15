"""Static evidence inventory, saved-pixel actor replay and actual-pose geometry.

Never constructs an environment, physics world, or hypothetical pose trajectory.
No actual296 position or pixel is inferred from another policy's episode.
"""
import argparse
import ast
import datetime
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from retry.path271_run import read,save,sha
from retry.pedal331_run import plain,digest


def rotate(p,a):
    c,s=math.cos(a),math.sin(a);return np.asarray(p)@np.array([[c,s],[-s,c]])


def world(local,body):return rotate(local,body['angle'])+body['position']
def local(points,body):return rotate(np.asarray(points)-body['position'],-body['angle'])
def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])
def wrap(a):return math.atan2(math.sin(a),math.cos(a))


def project(point,a,b):
    point,a,b=map(np.asarray,(point,a,b));delta=b-a;den=float(delta@delta);t=float(np.clip((point-a)@delta/den,0,1)) if den else 0.;closest=a+t*delta
    return float(np.linalg.norm(point-closest)),closest,t


def signed_polygon_distance(point,polygon):
    point=np.asarray(point);p=np.asarray(polygon);signs=[cross(b-a,point-a) for a,b in zip(p,np.roll(p,-1,axis=0))]
    inside=all(s>=0 for s in signs) or all(s<=0 for s in signs)
    d=min(project(point,a,b)[0] for a,b in zip(p,np.roll(p,-1,axis=0)))
    return -d if inside else d


def source_footprints(path):
    wanted={'SIZE','HULL_POLY1','HULL_POLY2','HULL_POLY3','HULL_POLY4','WHEEL_W','WHEEL_R'};values={}
    for statement in ast.parse(path.read_text()).body:
        if isinstance(statement,ast.Assign):
            for target in statement.targets:
                if isinstance(target,ast.Name) and target.id in wanted:values[target.id]=ast.literal_eval(statement.value)
    assert set(values)==wanted
    hull=[np.asarray(values['HULL_POLY'+str(i)],float)*values['SIZE'] for i in range(1,5)]
    w,r=values['WHEEL_W']*values['SIZE'],values['WHEEL_R']*values['SIZE'];wheel=np.array([[-w,r],[w,r],[w,-r],[-w,-r]])
    return hull,wheel


def road_reference(snapshot):
    roads=sorted(snapshot['roads'],key=lambda r:r['idx']);centers=np.array([world(r['fixture']['geometry']['vertices'],r['body']).mean(0) for r in roads]);ids=[r['idx'] for r in roads]
    return centers,ids


def road_projection(point,centers,ids,orientation):
    options=[(project(point,a,b),i) for i,(a,b) in enumerate(zip(centers,np.roll(centers,-1,axis=0)))];(distance,closest,fraction),i=min(options,key=lambda e:e[0][0]);delta=centers[(i+1)%len(centers)]-centers[i];length=float(np.linalg.norm(delta));tangent=delta/length*orientation
    arclength=sum(float(np.linalg.norm(b-a)) for a,b in zip(centers[:i],centers[1:i+1]))+fraction*length
    return dict(tile_pair=[ids[i],ids[(i+1)%len(ids)]],distance_m=distance,signed_lateral_m=cross(tangent,np.asarray(point)-closest),s_m=arclength,tangent=tangent.tolist(),projected_position=closest.tolist())


def geometry(snapshot,response,footprints,reference,orientation):
    hull_body=snapshot['hull'];centers,ids=reference;projection=road_projection(hull_body['position'],centers,ids,orientation)
    right=rotate([1.,0.],hull_body['angle']);forward=rotate([0.,1.],hull_body['angle']);velocity=np.array(hull_body['velocity']);vf=float(velocity@forward);vr=float(velocity@right)
    road_heading_error=math.atan2(cross(projection['tangent'],forward),float(np.dot(projection['tangent'],forward)))
    obstacles=[dict(index=i,center=world(o['fixture']['geometry']['pos'],o['body']).tolist(),radius=o['fixture']['radius']) for i,o in enumerate(snapshot['obstacles'])]
    polygons=[world(p,hull_body) for p in footprints[0]];wheels=[world(footprints[1],w['body']) for w in snapshot['wheels']]
    clearances=[]
    path=np.asarray(response['pixel_path'],float).reshape(-1,2)
    for obstacle in obstacles:
        center=np.array(obstacle['center']);bodycenter=local(center,hull_body)
        hull_distances=[signed_polygon_distance(center,p)-obstacle['radius'] for p in polygons]
        wheel_distances=[signed_polygon_distance(center,p)-obstacle['radius'] for p in wheels]
        nearest_path=min((project(bodycenter,a,b)[0] for a,b in zip(path[:-1],path[1:])),default=None)
        clearances.append(dict(obstacle=obstacle['index'],GT_body_center=bodycenter.tolist(),radius=obstacle['radius'],hull_core_gap_m=min(hull_distances),hull_fixture_core_gaps_m=hull_distances,
            wheel_core_gap_m=min(wheel_distances),wheel_core_gaps_m=wheel_distances,planned_centerline_to_GT_circle_gap_m=None if nearest_path is None else nearest_path-obstacle['radius'],
            planned_circumscribed_2_6m_gap_proxy=None if nearest_path is None else nearest_path-obstacle['radius']-2.6))
    direct=response['direct_obstacles'];tracked=[h[:3] for h in response['state']['hazards']]
    matching={}
    for name,observed in [('direct',direct),('tracked',tracked)]:
        matching[name]=[dict(observed=o,nearest_GT_obstacle=min(clearances,key=lambda c:np.linalg.norm(np.array(c['GT_body_center'])-o[:2]))['obstacle'],
            nearest_GT_center_error_m=min(float(np.linalg.norm(np.array(c['GT_body_center'])-o[:2])) for c in clearances)) for o in observed]
    tangent=next((p for p in path[1:] if np.linalg.norm(p)>0),None);path_heading=None if tangent is None else math.atan2(tangent[0],tangent[1]);slip=math.atan2(vr,vf)
    return dict(time=snapshot['actual_time'],position=hull_body['position'],angle=hull_body['angle'],speed_m_s=float(np.linalg.norm(velocity)),forward_velocity_m_s=vf,lateral_velocity_m_s=vr,slip_angle_rad=slip,
        road_tile_centerline_proxy=projection,road_heading_error_rad=road_heading_error,nearest_road_tiles=[w['tiles'] for w in snapshot['wheels']],
        planned_initial_heading_clockwise_rad=path_heading,velocity_heading_minus_planned_rad=None if path_heading is None else wrap(slip-path_heading),
        desired_curvature_clockwise=response['features'][5],actual_curvature_clockwise=None if abs(vf)<1e-12 else -hull_body['angular_velocity']/vf,
        steering_joint=[w['joint']['angle'] for w in snapshot['wheels'][:2]],actuator_targets=[w['dynamics']['steer'] for w in snapshot['wheels'][:2]],
        obstacles=clearances,nearest_perception_matches=matching,collision_contacts=snapshot['touching_obstacle_contacts'],
        footprint_scope='Source-defined local fixture cores transformed by actual captured body poses; actual car fixtures and polygon skin were not captured. No source world created.')


def inventory(R):
    sources={
        '296_success':dict(folder='stage294/policies/g1p4/N2',actions=363,precontact_boundary_last=64,first_contact=65,pixels=False,GT_pose=False,path=False,obstacle_GT=False,fixtures=False,features16=True,collision_damage=True),
        '330_failure':dict(folder='stage330/evaluation/N2',actions=72,pixel_stacks=73,precontact_boundary_last=67,first_contact=68,pixels=True,GT_pose=False,path=False,obstacle_GT=False,fixtures=False,features16=True,collision_damage=True),
        '331_A':dict(folder='stage331/A',actions=72,pixel_stacks=73,precontact_boundary_last=67,first_contact=68,pixels=True,GT_pose='boundary64; pre/post65-72 only',path=False,obstacle_GT='same boundaries',fixtures='road/obstacle fixtures captured; car fixture cores source-defined only',features16=True,collision_damage=True),
        '331_B':dict(folder='stage331/B',actions=72,pixel_stacks=73,precontact_boundary_last=67,first_contact=68,pixels=True,GT_pose='boundary64; pre/post65-72 only',path=False,obstacle_GT='same boundaries',fixtures='road/obstacle fixtures captured; car fixture cores source-defined only',features16=True,collision_damage=True)}
    for info in sources.values():
        folder=R/info['folder'];info['available_original_files']=[f.name for f in folder.iterdir() if f.is_file()];rows=[json.loads(s) for s in (folder/'trace-private.jsonl').read_text().splitlines()];assert len(rows)==info['actions'];info['contact_steps']=[r['step'] for r in rows if r['collision']];info['first_contact']=info['contact_steps'][0]
    return sources


def run(R):
    from retry.frozen_composite_runtime import prepare
    G=Path(__file__).resolve().parent.parent;D=R/'stage332';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'actor-opening.json').exists()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    config=read(R/'stage330/artifacts-private.json')['ON'];config.update(worker_path=str(G/'retry/diagnostic332_worker.py'),worker_sha256=sha(G/'retry/diagnostic332_worker.py'))
    save(D/'build-private.json',dict(config=config,runner_sha256=sha(Path(__file__)),source_hashes={str(G/'retry'/f):sha(G/'retry'/f) for f in ['diagnostic332_worker.py','diagnostic332_run.py']},new_fits=0))
    save(D/'inventory-private.json',inventory(R));save(D/'actor-opening.json',dict(epoch=time.time(),native_actions=0));start,cpu=time.perf_counter(),time.process_time();actorcpu=0.;calls=0;outputs={};reaped=[]
    for label in ['A','B']:
        F=R/'stage331'/label;z=np.load(F/'raw-pixels-actions-private.npz');old=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()];w=prepare(config,D/label/'cpu',p_source_sandbox(R));records=[]
        try:
            w.call('reset',z['observations'][0])
            for i in range(68):
                assert calls<p['caps']['actor_replay_calls_max'];r,_=w.call('act',z['observations'][i]);calls+=1
                assert r['action']==old[i]['calculated330'] and r['features']==old[i]['features'] and r['delta_audit']==old[i]['audit'],(label,i,'actor mismatch')
                c,_=w.call('commit',z['actions'][i]);assert c['memory']==old[i]['nominal_memory'] and c['state']==old[i]['policy'],(label,i,'state mismatch')
                actorcpu=c['actor_cumulative_CPU_s'];records.append(dict(boundary=i,step=i+1,response=r,executed=old[i]['executed']))
            outputs[label]=records
        finally:reaped.append(w.close())
        save(D/label/'saved-pixel-replay-private.json',plain(records));actorcpu_total=locals().get('actorcpu_total',0.)+actorcpu
    save(D/'actor-cost.json',dict(saved_observation_actor_calls=calls,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu_total,reaping=reaped,native_actions=0,new_fits=0,source_physics_rollout_ticks=0))
    tick,geomcpu=time.perf_counter(),time.process_time();footprints=source_footprints(G/'core/vendor/car_dynamics.py');base=read(R/'stage331/A/boundary-private.json')['physical'];reference=road_reference(base);projection=road_projection(base['hull']['position'],*reference,1.);forward=rotate([0.,1.],base['hull']['angle']);orientation=1. if np.dot(projection['tangent'],forward)>=0 else -1.
    geometries={}
    for label in ['A','B']:
        old=[json.loads(s) for s in (R/'stage331'/label/'trace-private.jsonl').read_text().splitlines()];measured=[]
        for boundary in range(64,68):
            snapshot=old[boundary]['pre_physical'];r=outputs[label][boundary]['response'];g=geometry(snapshot,r,footprints,reference,orientation);g.update(boundary=boundary,action=boundary+1,command=old[boundary]['executed']);measured.append(g)
        geometries[label]=measured
    alignment=[]
    for x in geometries['A']:
        candidates=[b for b in geometries['B'] if b['road_tile_centerline_proxy']['tile_pair']==x['road_tile_centerline_proxy']['tile_pair']]
        y=min(candidates,key=lambda y:np.linalg.norm(np.array(y['position'])-x['position'])) if candidates else None
        alignment.append(dict(A_boundary=x['boundary'],B_boundary=None if y is None else y['boundary'],tile_pair=x['road_tile_centerline_proxy']['tile_pair'],nearest_observed_position_gap_m=None if y is None else float(np.linalg.norm(np.array(y['position'])-x['position'])),
            longitudinal_proxy_gap_m=None if y is None else y['road_tile_centerline_proxy']['s_m']-x['road_tile_centerline_proxy']['s_m'],
            speed_difference_B_minus_A=None if y is None else y['speed_m_s']-x['speed_m_s'],heading_difference_B_minus_A=None if y is None else wrap(y['angle']-x['angle'])))
    save(D/'geometry-private.json',plain(dict(actual_precontact_geometries=geometries,spatial_alignment=alignment,full_296_vs_failure_spatial_alignment_available=False,source_nominal_hull_wheel_footprints=[ [a.tolist() for a in footprints[0]],footprints[1].tolist()],road_proxy='Saved road fixture centroids joined by tile index; not raw.track and not an exact racing line.',orientation=orientation)))
    save(D/'geometry-cost.json',dict(wall_s=time.perf_counter()-tick,runner_CPU_s=time.process_time()-geomcpu,actual_boundaries=8,native_actions=0,new_fits=0,source_physics_rollout_ticks=0))
    print(json.dumps(dict(saved_pixel_calls=calls,actual_precontact_boundaries=8,spatial_matches=len([x for x in alignment if x['B_boundary'] is not None]),native=0,fit=0,rollout=0)),flush=True)


def p_source_sandbox(R):return read(R/'stage331/plan.json')['sandbox_path']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);run(p.parse_args().private_root)
